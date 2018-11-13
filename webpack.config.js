/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/* eslint-env node */
/* eslint-disable import/no-extraneous-dependencies */

const path = require('path');
const webpack = require('webpack');
const merge = require('webpack-merge');

const ROOT_DIR = path.resolve(__dirname);
const BUILD_DIR = path.resolve(ROOT_DIR, 'build');

const common = {
  target: 'web',
  mode: 'development',
  context: ROOT_DIR,
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
  resolve: {
    extensions: ['.js', '.jsx'],
    alias: {
      training: path.resolve(ROOT_DIR, 'js'),
    },
  },
};

module.exports = [
  merge(common, {
    entry: {
      freeze: './js/freeze',
      train: './js/train',
    },
    plugins: [
      new webpack.BannerPlugin({
        banner: 'const marionetteArguments = arguments;',
        raw: true,
        entryOnly: true,
      }),
    ],

  }),
  merge(common, {
    entry: {
      train_framescript: './js/train_framescript',
    },
    plugins: [
      new webpack.BannerPlugin({
        banner: 'const global = this;',
        raw: true,
        entryOnly: true,
      }),
    ],
  }),
];
