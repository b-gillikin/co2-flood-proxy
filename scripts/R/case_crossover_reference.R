# Reference fit of the primary case-crossover model in R (protocol §7).
#
# The cross-basis and predictions use dlnm. Coefficients come from a Poisson
# GLM with one fixed effect per stratum, which gives the same coefficients as
# the conditional Poisson likelihood (Armstrong, Gasparrini and Tobias 2014).
# gnm's eliminate= fit, the usual fast route, is also attempted and its
# convergence recorded, because it diverged on some simulated datasets.
#
# Used only to validate the Python estimator on synthetic data
# (scripts/38_validate_estimator.py). Reads one hourly table with columns
# watercourse, hour, rain, warm, onset, at_risk, stratum, and writes the
# season-specific lag curves and summaries at the given rainfall contrast.
#
# Usage: Rscript scripts/R/case_crossover_reference.R input.csv output.csv contrast

suppressMessages({
  library(dlnm)
  library(gnm)
})

args <- commandArgs(trailingOnly = TRUE)
input <- args[1]
output <- args[2]
contrast <- as.numeric(args[3])

d <- read.csv(input)
d <- d[order(d$watercourse, d$hour), ]
knots <- logknots(c(1, 72), fun = "ns", df = 4)
cb <- crossbasis(
  d$rain,
  lag = c(1, 72),
  argvar = list(fun = "lin"),
  arglag = list(fun = "ns", knots = knots),
  group = d$watercourse
)

# Lag alignment: a unit spike at row i must enter row i + 1 as lag 1.
spike <- crossbasis(c(rep(0, 80), 1, rep(0, 80)), lag = c(1, 72),
  argvar = list(fun = "lin"), arglag = list(fun = "ns", knots = knots))
lag_basis <- onebasis(1:72, fun = "ns", knots = knots, Boundary.knots = c(1, 72), intercept = TRUE)
stopifnot(isTRUE(all.equal(as.numeric(spike[82, ]), as.numeric(lag_basis[1, ]))))
stopifnot(all(spike[81, ] == 0), all(spike[81 + 73, ] == 0))

x <- matrix(as.numeric(cb), nrow(cb))
warm_x <- x * d$warm
cold_x <- x * (1 - d$warm)

# Strata with no onset among complete at-risk rows carry no information.
use <- d$at_risk == 1 & complete.cases(x)
informative <- tapply(d$onset[use], d$stratum[use], sum) > 0
use <- use & d$stratum %in% names(informative)[informative]

dd <- d[use, ]
wx <- warm_x[use, ]
cx <- cold_x[use, ]
fit <- glm(dd$onset ~ wx + cx + factor(dd$stratum) - 1, family = poisson(),
  control = glm.control(epsilon = 1e-12, maxit = 200))
n <- ncol(x)
beta <- coef(fit)[1:(2 * n)]
covariance <- vcov(fit)[1:(2 * n), 1:(2 * n)]
dispersion <- sum(residuals(fit, type = "pearson")^2) / fit$df.residual

gnm_fit <- try(gnm(onset ~ warm_x + cold_x - 1, eliminate = factor(stratum),
  family = quasipoisson(), data = d, subset = use), silent = TRUE)
gnm_status <- if (inherits(gnm_fit, "try-error")) "failed" else "converged"
gnm_max_difference <- if (gnm_status == "converged") max(abs(coef(gnm_fit) - beta)) else NA

rows <- list()
for (season in c("warm", "cold")) {
  idx <- if (season == "warm") 1:n else (n + 1):(2 * n)
  pred <- crosspred(cb, coef = beta[idx], vcov = covariance[idx, idx],
    model.link = "log", at = contrast, cen = 0, cumul = TRUE)
  curve <- as.numeric(pred$matfit) / contrast
  cumulative <- as.numeric(pred$cumfit)
  total <- as.numeric(pred$allfit)
  median_lag <- if (total > 0) which(cumulative >= total / 2)[1] else NA
  rows[[season]] <- data.frame(
    season = season, lag = 1:72, log_rr_per_unit = curve,
    cumulative_log_rr = total, median_lag = median_lag,
    dispersion = dispersion, n_rows = sum(use),
    n_onsets = sum(d$onset[use]), gnm_status = gnm_status,
    gnm_max_coef_difference = gnm_max_difference
  )
}
write.csv(do.call(rbind, rows), output, row.names = FALSE)
