# Disaster recovery

The chapter's immutable inputs are copied to a dedicated private Azure GZRS
storage account. GitHub remains the recovery source for code and documentation.
The backup is additive: deleting a local file cannot delete its remote copy,
and Azure blob versioning retains overwritten objects.

```bash
make recovery-doctor
make data-inventory
make data-backup
make data-verify
make data-restore  # on a replacement machine; preserves existing local files
```

Run `az login` on a replacement machine. Access uses the signed-in Microsoft
Entra identity and is restricted to the backup account; storage keys and SAS
tokens are not stored in this repository.

The manifest is evidence of the exact bytes backed up. A checksum alone is not
a backup; successful `data-backup` and a periodic clean restore test are the
recovery controls.
