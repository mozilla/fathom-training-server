/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/* eslint-env node */
/* eslint-disable import/no-extraneous-dependencies */

const path = require('path');
const webpack = require('webpack');

const ROOT_DIR = path.resolve(__dirname);
const BUILD_DIR = path.resolve(ROOT_DIR, 'build');

module.exports = {
  target: 'web',
  mode: 'development',
  context: ROOT_DIR,
  entry: {
    freeze: './js/freeze',
  },
  output: {
    path: BUILD_DIR,
    filename: '[name].bundle.js',
  },
  module: {
    rules: [
      // jsdom is imported by fathom-web utils.js; it's only used for testing
      {
        test: /jsdom.*/,
        use: {
          loader: 'null-loader',
        },
      },
    ],
  },
  node: {
    fs: 'empty',
  },
  plugins: [
    new webpack.BannerPlugin({
      banner: 'const marionetteScriptFinished = arguments[0];',
      raw: true,
      entryOnly: true,
    }),
  ],
  resolve: {
    extensions: ['.js', '.jsx'],
    alias: {
      training: path.resolve(ROOT_DIR, 'js'),
    },
  },
};
