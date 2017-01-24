
# Set the initial environment for building and developing the app.

# This should be sourced:
# . ./initenv.sh

BUILD_PATH=build
# npm_config_prefix="$BUILD_PATH/node_modules"
# NODE_PATH="$npm_config_prefix/lib/node_modules"

PATH="./node_modules/.bin:$PATH"

# export PATH BUILD_PATH npm_config_prefix NODE_PATH
export PATH BUILD_PATH
