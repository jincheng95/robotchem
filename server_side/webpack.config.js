var webpack = require('webpack');

module.exports = {
    devtool: 'eval',
    entry: './app/index.js',
    output: {
        filename: 'bundle.js',
        path: './static'
    },

    module: {
        loaders: [
            {test: /\.js$/, exclude: /node_modules/, loader: "babel-loader"},
            {test: /\.css$/, loader: 'style!css?modules', include: /flexboxgrid/},
        ]
    },


      plugins: [
        new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
      ]
};