#!/bin/bash
set -xe

# This asumes it's running inside tpa code, next to the requirements
# files. "/out" is the shared directory between the host and this
# container that can be used

: "${DISTRO:?DISTRO environment variable is required}"
# DISTRO_ARCHITECTURE is the architecture of the target system
: "${DISTRO_ARCHITECTURE:?DISTRO_ARCHITECTURE environment variable is required}"
# FILENAME_SUFFIX is usually empty or "-rh8"
: "${FILENAME_SUFFIX?FILENAME_SUFFIX environment variable is required}"

DEFAULT_EDBPYTHON="edb-python312"
FORCE_REBUILD_PYMODULES="${FORCE_REBUILD_PYMODULES:-0}"
PYTHON="/usr/libexec/${DEFAULT_EDBPYTHON}/bin/python"
PIP_DEST="pip-packages"
VENV="newpip"
PIP="$VENV/bin/pip3"

function install_edbpython_inside_container() {
    case $DISTRO in
        "deb")
            SUFFIX="deb"
            CMD="apt"
	    DEPS=""
	;;
        "el")
            SUFFIX="rpm"
            CMD="yum"
	    DEPS="$DEFAULT_EDBPYTHON-devel openssl-devel"
	;;
    esac

    curl --proto "=https" -1sLf "https://downloads.enterprisedb.com/${EDB_SUBSCRIPTION_TOKEN}/dev/setup.${SUFFIX}.sh" | sudo bash
    sudo "$CMD" install -y $DEFAULT_EDBPYTHON $DEPS

    # Install Rust using the installation script to ensure newer version than
    # the one available in package manager's repositories
    if [[ $DISTRO = "el" ]] ; then
        sudo curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    fi

}

function create_venv_and_prep_stuff {
    # install and setup python venv
    $PYTHON -m venv $VENV
    mkdir -p "$PIP_DEST"
    $PIP install --upgrade pip pip-tools wheel
    #$PIP download --dest "$PIP_DEST" pip wheel
    # Add EDB repositories as index to ensure the already generated wheels for
    # this specific architecture are available as dependencies for the base
    # environment such as cloudsmith cli (needs cryptography)
    #
    # cloudsmith-cli pulls in its own compiled dependencies (cryptography,
    # pycryptodome, argon2-cffi-bindings via keyrings-cryptfile) that have no
    # prebuilt wheel for this architecture, so pip has to build them from
    # source. Building into $PIP_DEST (instead of a plain `pip install`)
    # means those wheels get picked up by check_any_wheel_created_and_upload
    # and published too, so future runs can reuse them instead of rebuilding
    # from source every time.
    $PIP wheel -w "$PIP_DEST" cloudsmith-cli \
        --extra-index-url=https://dl.cloudsmith.io/public/cloudsmith/cli/python/index/ \
        --extra-index-url="https://downloads.enterprisedb.com/$TPA_PIP_CS_API/build-dependencies/python/simple/"
    $PIP install --no-index --find-links "$PIP_DEST" cloudsmith-cli
}

function check_any_wheel_created_and_upload {
    # upload any new wheel we generated
    find $PIP_DEST -name \*.whl -print -exec \
	    $VENV/bin/cloudsmith push python --error-retry-max 5 \
            --api-key "$CLOUDSMITH_BUILD_DEPENDENCIES_API_KEY" -v \
            enterprisedb/build-dependencies {} \;
}

function generate_new_requirements_file {
    # generate the new txt file using our index repo that holds newly built dependencies for the arch
    requirement_txt_file="$(echo -n "$1" | sed "s/\.in/.txt/g")"

    $VENV/bin/pip-compile --generate-hashes \
	    --index-url="https://downloads.enterprisedb.com/$TPA_PIP_CS_API/build-dependencies/python/simple/" \
	    --no-emit-options \
	    --no-header \
	    --output-file "$requirement_txt_file" \
	    --strip-extras "$1"
}

# generate the new arch specific requirement files
current_arch_file="requirements-${DISTRO_ARCHITECTURE}${FILENAME_SUFFIX}.in"
output_requirements_include="/out/requirements-${DISTRO_ARCHITECTURE}${FILENAME_SUFFIX}.in"
first_new_detected=0

# read the .in file line by line
while IFS= read -r requirement_line
do
    echo "$requirement_line"
    target_module_name=$(echo -n "$requirement_line" | cut -d '=' -f1)
    target_module_version=$(echo -n "$requirement_line" | cut -d '=' -f3|xargs)
    # shellcheck disable=SC1003
    requirement_module_version=$(grep ^"$target_module_name" requirements${FILENAME_SUFFIX}.txt | cut -d '=' -f3 | cut -d '\' -f1|xargs)

    echo "Comparing version of base $requirement_module_version with target arch version $target_module_version"
	if [ $FORCE_REBUILD_PYMODULES == "true" ] || [ "$requirement_module_version" != "$target_module_version" ]; then
    #If module version in requirements.txt is found but different than the one present
    #in target arch file, ie: requirements-ppc64.in then we should build and stick
    #to what requirements.txt needs
        echo "Version ($requirement_module_version) detected for $target_module_name"
        # populate a new arch specific file
        echo "$target_module_name==$requirement_module_version" >> $output_requirements_include
        if [ $first_new_detected == 0 ]; then
            first_new_detected=1
            install_edbpython_inside_container
            create_venv_and_prep_stuff
	    fi
        #Asume that we we found is new hence, doesn't exist in our private repo and a new build
	    #if required
        # Adding EDB cloudsmith repo as index here to, ensure that we won't try
        # to build already generated wheel file for a dependency, allowing to
        # cut execution time.
        $PIP wheel -w $PIP_DEST --no-deps \
            --extra-index-url="https://downloads.enterprisedb.com/$TPA_PIP_CS_API/build-dependencies/python/simple/" \
            "$target_module_name==$requirement_module_version"
    else
        # dep is unchanged, add it back to the new file
        echo "$requirement_line" >> $output_requirements_include
    fi
done < $current_arch_file

if [ $first_new_detected == "0" ]; then
    echo "No new dependencies detected, nothing to do"
    exit 0
fi

check_any_wheel_created_and_upload
generate_new_requirements_file $output_requirements_include
