These handlers may be fired to manage the PostgreSQL service.

Note that Ansible by default fires handlers in the order they're written, not
the order they're notified, and does so at the end of the play.

You can force them to fire with `meta: flush_handlers` but that's like a global
`sync`, it flushes *everything*.

Another option is to just use an `include` directive to pull in the handler task
directly.
