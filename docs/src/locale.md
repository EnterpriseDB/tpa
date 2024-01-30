# Locale

For some platform images and environments, you might want to
set the region and language settings.

By default, tpaexec installs the `en_US.UTF-8` locale system files.
You can set the desired locale in your `config.yml`:

```yaml
user_locale: en_GB.UTF-8
```

To see the supported locales, use the following command:

```shell
localectl list-locales
```

Alternatively, on Debian or Ubuntu, look at the contents of the file `/etc/locales.defs`.
