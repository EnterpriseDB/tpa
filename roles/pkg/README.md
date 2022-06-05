# Package installation

Any xxx/pkg role should be organised as described below.

## Highlights

- Anyone can call a pkg role's list-packages.yml to get a list of
  packages to be installed for a given role on the current instance,
  e.g., ['etcd'] on an etcd instance, and [] on a non-etcd instance

- xxx/pkg/tasks/main.yml is the main caller of …/list-packages, and
  pkg/list_all_packages is another (used by download-packages)

- Every pkg role just assembles its own list and calls pkg/install to
  install the packages

## Layout examples

First, defaults/main.yml typically defines some distribution-dependent
package lists:

    xxx_packages:
        Debian: &debian_xxx_packages
          - xxx
          - yyy
        RedHat:
          - xxx1
          - yyy2-{{ zzz }}
        Ubuntu: *debian_xxx_packages

(The &debian_xxx_packages notation creates a YAML "anchor": this example
sets the contents of the Ubuntu list to be the same as the Debian list.)

If required, these default lists may be indexed by more than just the
ansible_distribution (e.g., postgres_family). Interpreting the default
list is the role's business, nobody else's.

Next, list-packages.yml is responsible for "returning" the
complete list of packages required for the xxx role. The return value is
conditional on the role (and other conditions) of the current instance.
So for example, barman/pkg's list-packages should return the expected
list of packages, but on a postgres instance, it should return [].

    - when: "'xxx' in role"
      block:
      # This is shorthand to add the list_contents to whichever
      # list_varname was passed in by our caller (see below).
      - include_role: name=pkg/add_to_list
        vars:
          # Fetch and evaluate the right list for the distribution
          list_contents: "{{
              xxx_packages|packages_for(
                  ansible_distribution, xxx_package_version
              )
          }}"

      # (You can include pkg/add_to_list multiple times if needed.)

      # If we need to include packages from another role, we can do so by
      # using its own list-packages.yml, which will add to the same list
      # because list_varname here is the value that was passed in to us.

      - include_role:
          name: yyy/pkg
          tasks_from: list-packages.yml

Finally, tasks/main.yml should look like this:

    - include_tasks: list-packages.yml
      vars:
        list_varname: _all_xxx_packages

    - include_role: name=pkg/install
      vars:
        package_list_name: "xxx packages"
        package_list: "{{ _all_xxx_packages }}"

It doesn't matter what list_varname you use, so long as some other role
isn't going to mess with its contents (hence `_all_xxx_packages` here).

It's helpful to define `_all_xxx_packages: []` in xxx/pkg/vars/main.yml
for roles with conditional list-packages, so that it's always defined,
even if list-packages doesn't see fit to add anything to it.
