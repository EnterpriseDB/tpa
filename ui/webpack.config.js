
var build_dir = process.env.BUILD_PATH ? process.env.BUILD_PATH
                    : ( __dirname+'/build' );
var node_modules = build_dir+'/node_modules/lib/node_modules';
var path = require('path');


module.exports = {
    entry: './fe/js/main.js',
    output: {
        path: build_dir+'/static',
        filename: 'bundle.js',
        publicPath: '/'
    },
    resolveLoader: {
        root: path.resolve(node_modules),
    },
    devtool: 'source-map', // or 'inline-source-map',
    module: {
        loaders: [
            // via: https://github.com/jtangelder/sass-loader
            {
                test: /\.scss$/,
                exclude: node_modules,
                loaders: ['style-loader', 'css-loader?SourceMap', 'sass-loader?sourceMap']
            },
            {
                test: /\.js$/,
                exclude: node_modules,
                loader: 'babel-loader',
                query: {
                    presets: ['es2015']
                }
            },
            {
                test: /\.css$/,
                exclude: node_modules,
                loader: 'style!css'
            },
        ]
    }
};
