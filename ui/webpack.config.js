const build_dir = process.env.BUILD_PATH ? process.env.BUILD_PATH
                    : ( __dirname+'/build' );

const path = require('path');
const webpack = require('webpack');
var HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
    entry: './fe/js/main.js',
    output: {
        path: build_dir+'/static',
        filename: 'bundle.[hash].js',
        publicPath: '/',
        libraryTarget: "var",
        library: "tpa"
    },
    resolve: {
        alias: {
            'vue$': 'vue/dist/vue.common.js'
        }
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
            }
        ]
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: './fe/index.html.ejs',
            filename: 'index.html',
            inject: 'body',
        }),
        new HtmlWebpackPlugin({
            template: './fe/cluster.html.ejs',
            filename: 'cluster.html',
            inject: 'body',
        }),
        new HtmlWebpackPlugin({
            template: './fe/cluster_upload.html.ejs',
            filename: 'cluster_upload.html',
            inject: 'body',
        }),
        new webpack.ProvidePlugin({
            d3: 'd3',
            $: 'jquery',
            jQuery: 'jquery',
            jquery: 'jquery'
        })
    ]
};
