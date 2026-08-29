# Disaster recovery

The chapter's immutable inputs are copied to private institutional OneDrive
storage. GitHub remains the recovery source for code and documentation. The
backup command uses `rclone copy`, never `sync`: deleting a local file cannot
delete the remote copy, and replaced remote objects are retained under
`_versions/`.

```bash
make recovery-doctor
make data-inventory
make data-backup
make data-verify
make data-restore  # on a replacement machine; preserves existing local files
```

Set `DISSERTATION_BACKUP_REMOTE` or `DISSERTATION_BACKUP_ROOT` to override the
defaults in `config.json`. Credentials belong in rclone's user configuration,
never in this repository.

The manifest is evidence of the exact bytes backed up. A checksum alone is not
a backup; successful `data-backup` and a periodic clean restore test are the
recovery controls.
