var webpack = require('webpack');
var path = require('path');
var WebpackCleanupPlugin = require('webpack-cleanup-plugin');


module.exports = {
	entry: [
		'babel-polyfill',
		'./app/index.js'
	],
	output: {
		path: path.join(__dirname, 'static'),
		filename: 'bundle.js'
	},
	resolve: {
		extensions: ['', '.js', '.jsx']
	},
	module: {
		loaders: [
				{test: /\.js$/, exclude: /node_modules/, loader: "babel-loader"},
				{test: /\.css$/, loader: 'style!css?modules', include: /flexboxgrid/},
		]
	},
	plugins: [
		new WebpackCleanupPlugin(),
		new webpack.DefinePlugin({
			'process.env': {
				NODE_ENV: '"production"'
			}
		}),
		new webpack.ContextReplacementPlugin(/moment[\/\\]locale$/, /en/),
		new webpack.optimize.UglifyJsPlugin({
			compress: {
				warnings: false,
				screw_ie8: true,
				drop_console: true,
				drop_debugger: true
			}
		}),
		new webpack.optimize.OccurenceOrderPlugin(),
		new webpack.optimize.DedupePlugin()
	]
};