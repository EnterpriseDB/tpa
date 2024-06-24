# Locale

For some platform images and environments it might be desirable to
set the region and language settings.

By default, TPAexec will install the `en_US.UTF-8` locale system files.
You can set the desired locale in your `config.yml`:

```yaml
user_locale: en_GB.UTF-8
```

To find supported locales consult the output of the following command:
```shell
localectl list-locales
```
Or the contents of the file /etc/locales.defs on Debian or Ubuntu.
