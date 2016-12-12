const build_dir = process.env.BUILD_PATH ? process.env.BUILD_PATH
                    : ( __dirname+'/build' );
const node_modules = build_dir+'/node_modules/lib/node_modules';

const path = require('path');

module.exports = {
    entry: './fe/js/main.js',
    output: {
        path: build_dir+'/static',
        filename: 'bundle.js',
        publicPath: '/'
    },
    resolve: {
        root: path.resolve(node_modules),
    },
    resolveLoader: {
        root: path.resolve(node_modules),
    },
    devtool: 'source-map',
    module: {
        loaders: [
            // via: https://github.com/jtangelder/sass-loader
            {
                test: /\.scss$/,
                loaders: ['style-loader',
                        'css-loader?SourceMap',
                        'sass-loader?SourceMap']
            },
            {
                test: /\.js$/,
                loader: 'babel-loader',
                query: {
                    presets: ['es2015']
                }
            },
            {
                test: /\.css$/,
                loader: 'style!css'
            },
        ]
    }
};
