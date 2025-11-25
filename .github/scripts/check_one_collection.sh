#!/bin/bash
#
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.
#
# takes two arguments:
# - a name of an Ansible Galaxy collection
# - a filename of a Galaxy requirements file, usually requirements.yml
#   or a variant of this
#
# updates the file with an updated version
# containing the latest version of the specified collection
#
# if a change is made:
# - appends a link to the changelog to the file in $CHANGELOG_PATH
# - writes "true" to the file in $FLAG_FILE
# else writes "false" to the file in $FLAG_FILE

export COLLECTION_NAME=$1
export COLLECTION_FILE=$2
GALAXY_API_PATH="https://galaxy.ansible.com/api/v3/plugin/ansible/content/published/collections/index"
CURRENT_VERSION=$(yq -r \
          '.collections[] | select(.name == env(COLLECTION_NAME)) | .version' \
          $COLLECTION_FILE)

if [ -z "$CURRENT_VERSION" ]; then
  echo "::error::Could not find version for $COLLECTION_NAME"
  exit 1
fi

echo "Found $COLLECTION_NAME version $CURRENT_VERSION"
COLLECTION_PATH="${COLLECTION_NAME/./\/}"
export UPSTREAM_VERSION=$(
  curl -sS "$GALAXY_API_PATH/$COLLECTION_PATH/versions/?ordering=is_highest"\
  | jq -r '[.data[] | .version | select(test("^[0-9.]+$"))][0]'
)

if [ -z "$UPSTREAM_VERSION" ]; then
  echo "::error::Could not find upstream version"
  exit 1
fi
echo "Found upstream version $UPSTREAM_VERSION"

# if the versions differ then it must be because the upstream is
# newer, no need to actually do a semver comparison
if [ "$CURRENT_VERSION" != "$UPSTREAM_VERSION" ]; then
  yq -i '(.collections[]
           | select(.name == env(COLLECTION_NAME)) |
           .version
         ) = env(UPSTREAM_VERSION)' $COLLECTION_FILE
  echo "Updated requirements.yml"

  # the standard location for a changelog is CHANGELOG.rst in main
  # but for community.general this is a placeholder, so we look in
  # the relevant stable branch
  CL_BRANCH=main
  if [ "$COLLECTION_NAME" == "community.general" ]; then
    CL_BRANCH="stable-${UPSTREAM_VERSION%%.*}"
  fi
  COLLECTION_REPOSITORY=$(
    curl -sS "$GALAXY_API_PATH/$COLLECTION_PATH/versions/$UPSTREAM_VERSION/" \
    | jq -r '.metadata.repository')
  CHANGELOG="$COLLECTION_REPOSITORY/blob/$CL_BRANCH/CHANGELOG.rst"

  echo $CHANGELOG >> $CHANGELOG_PATH
  echo "true" > $FLAG_FILE
else
  echo "false" > $FLAG_FILE
fi
