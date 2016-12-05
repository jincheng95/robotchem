

module.exports = {
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

};