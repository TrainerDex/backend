const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  entry: {home: './assets/src/home'},
  output: {
    path: path.resolve('./assets/webpack_bundles/'),
    filename: '[name].bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        options: {presets: ['@babel/preset-env', '@babel/preset-react']},
      },
    ],
  },
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],
};
