const build_dir = process.env.BUILD_PATH ? process.env.BUILD_PATH
                    : ( __dirname+'/build' );
const node_modules = build_dir+'/node_modules/lib/node_modules';

const path = require('path');
const webpack = require('webpack');

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
                    presets: ['es2015'],
                    //plugins: ['transform-es2015-modules-umd']
                }
            },
            {
                test: /\.css$/,
                loader: 'style!css'
            },
            // via: http://reactkungfu.com/2015/10/integrating-jquery-chosen-with-webpack-using-imports-loader/
            {
                test: /(bootstrap|metismenu)\/.+\.(jsx|js)$/,
                loader: 'imports?jQuery=jquery,$=jquery,this=>window'
            },
            {
                test: /metisMenu\.js$/,
                loader: 'imports?jQuery=jquery,$=jquery,this=>window'
            },
            {
                test: /.jpe?g$|.gif$|.png$|.svg$|.woff$|.woff2$|.ttf$|.eot$/,
                loader: "url"
            },
        ],
        plugins: [
            new webpack.ProvidePlugin({
                d3: 'd3',
                $: 'jquery',
                jQuery: 'jquery',
                jquery: 'jquery'
            })
        ]
    }
};
