# Setting up Multi-tenancy
If you are in development and want to develop with multiple sites installed, yo have to setup multi-tenancy using the hosts file.
This will behave similarly to [multi-tenancy based on DNS in production](https://frappeframework.com/docs/user/en/bench/guides/setup-multitenancy).

For each site run the following script

```sh
bench --site sitename add-to-hosts
```
