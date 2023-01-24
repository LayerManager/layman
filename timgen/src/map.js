/**

Inspired by https://github.com/hslayers/hslayers-ng
Modified heavily by @jirik

The MIT License

Copyright (c) 2010-2015 CCSS, http://ccss.cz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

 */

import ol_Map from 'ol/Map';
import * as ol_proj from 'ol/proj';
import ol_View from 'ol/View';
import ol_source_ImageWMS from 'ol/source/ImageWMS';
import ol_source_TileWMS from 'ol/source/TileWMS';
import ol_layer_Image from 'ol/layer/Image';
import ol_layer_Tile from 'ol/layer/Tile';

const json_to_extent = (value) => {
  if (typeof value === 'string') {
    value = value.split(" ");
  }
  value = value.map(v => parseFloat(v));
  return value;
};


const proxify = (requested_url) => {
  const proxy = requested_url.startsWith('https://') ? 'https' : 'http';
  return `http://${window.location.hostname}:8080/${proxy}_proxy?url=${encodeURIComponent(requested_url)}`;
};


export const adjust_map_url = (requested_url) => {
  return proxify(requested_url);
};


const adjust_layer_url = (requested_url, gs_public_url, gs_url) => {
  if(gs_public_url && gs_url && requested_url.startsWith(gs_public_url)) {
    const old = requested_url;
    requested_url = requested_url.replace(gs_public_url, gs_url);
    log(`replaced layer URL ${old} with ${requested_url}`);
  }
  return proxify(requested_url);
};


const proxify_layer_loader = (layer, tiled, gs_public_url, gs_url, headers) => {
  const source = layer.getSource();

  const load_fn = (tile_or_img, image_url) => {
    const adjusted_image_url = adjust_layer_url(image_url, gs_public_url, gs_url);
    log(`load_fn, image_url=${image_url} adjusted_image_url=${adjusted_image_url}`)
    fetch(adjusted_image_url, {
      headers,
    }).then(res => {
      log(`load_fn, res.status=${res.status}, image_url=${image_url}`)
      return res.blob();
    }).then(blob => {
      const data_url = URL.createObjectURL(blob);
      log(`load_fn, blob loaded`)
      tile_or_img.getImage().src = data_url;
    })
  };

  if (tiled) {
    source.setTileLoadFunction(load_fn);
  } else {
    source.setImageLoadFunction(load_fn);
  }
};


const json_to_wms_layer = (layer_json, gs_public_url, gs_url, headers) => {
  const source_class = layer_json.singleTile ? ol_source_ImageWMS : ol_source_TileWMS;
  const layer_class = layer_json.singleTile ? ol_layer_Image : ol_layer_Tile;
  const params = layer_json.params;
  const legends = [];
  delete params.REQUEST;
  //delete params.FORMAT; Commented, because otherwise when loading from cookie or store, it displays jpeg
  const new_layer = new layer_class({
    // title: layer_json.title,
    // from_composition: true,
    maxResolution: layer_json.maxResolution || Number.Infinity,
    minResolution: layer_json.minResolution || 0,
    // minScale: layer_json.minScale || Number.Infinity,
    // maxScale: layer_json.maxScale || 0,
    // show_in_manager: layer_json.displayInLayerSwitcher,
    // abstract: layer_json.name || layer_json.abstract,
    // base: layer_json.base,
    // metadata: layer_json.metadata,
    // dimensions: layer_json.dimensions,
    // saveState: true,
    // path: layer_json.path,
    opacity: layer_json.opacity || 1,
    source: new source_class({
      url: decodeURIComponent(layer_json.url),
      // attributions: layer_json.attribution ? [new ol.Attribution({
      //   html: '<a href="' + layer_json.attribution.OnlineResource + '">' + layer_json.attribution.Title + '</a>'
      // })] : undefined,
      // styles: (angular.isDefined(layer_json.metadata) ? layer_json.metadata.styles : undefined),
      params: params,
      crossOrigin: 'anonymous',
      projection: layer_json.projection,
      // ratio: layer_json.ratio
    })
  });
  new_layer.setVisible(layer_json.visibility);
  proxify_layer_loader(new_layer, !layer_json.singleTile, gs_public_url, gs_url, headers);
  return new_layer;

};


const json_to_layer = (layer_json, gs_public_url, gs_url, headers) => {
  switch (layer_json.className) {
    case "HSLayers.Layer.WMS":
      return json_to_wms_layer(layer_json, gs_public_url, gs_url, headers);
      break;
    // case 'OpenLayers.Layer.Vector':
    //   return configParsers.createVectorLayer(layer_json);
    //   break;
    default:
      log(`Unsupported layer className ${layer_json.className}`);
      break;
  }
};


const json_to_layers = (layers_json, gs_public_url, gs_url, headers) => {
  if (layers_json.data) {
    layers_json = layers_json.data;
  }
  return layers_json.map(lj => json_to_layer(lj, gs_public_url, gs_url, headers));
};


export const json_to_map = ({
                              map_json,
                              gs_url,
                              gs_public_url,
                              headers,
                            }) => {

  const ol_map = new ol_Map({
    target: 'map',
    controls: [],
    layers: [
      // new TileLayer({
      //   source: new OSM()
      // })
    ],
    view: new ol_View({
      center: [0, 0],
      zoom: 0
    })
  });


  // log('load_map', map_json);
  const view = ol_map.getView();

  const extent_4326 = json_to_extent(map_json.extent);
  // log('extent_4326', extent_4326);
  const extent = ol_proj.transformExtent(extent_4326, 'EPSG:4326', view.getProjection());
  // log('extent', extent);
  view.fit(extent, {
    constrainResolution: false
  });

  const layers = json_to_layers(map_json.layers, gs_public_url, gs_url, headers);
  layers.forEach(layer => {
    if(layer) {
      ol_map.addLayer(layer);
    }
  });

  return ol_map;
};


export const map_to_canvas = (map) => {
  // see https://openlayers.org/en/latest/examples/export-map.html
  const mapCanvas = document.createElement('canvas');
  const size = map.getSize();
  mapCanvas.width = size[0];
  mapCanvas.height = size[1];
  const mapContext = mapCanvas.getContext('2d');
  Array.prototype.forEach.call(
      map.getViewport().querySelectorAll('.ol-layer canvas, canvas.ol-layer'),
      function (canvas) {
        if (canvas.width > 0) {
          const opacity =
              canvas.parentNode.style.opacity || canvas.style.opacity;
          mapContext.globalAlpha = opacity === '' ? 1 : Number(opacity);
          let matrix;
          const transform = canvas.style.transform;
          if (transform) {
            // Get the transform parameters from the style's transform matrix
            matrix = transform
                .match(/^matrix\(([^\(]*)\)$/)[1]
                .split(',')
                .map(Number);
          } else {
            matrix = [
              parseFloat(canvas.style.width) / canvas.width,
              0,
              0,
              parseFloat(canvas.style.height) / canvas.height,
              0,
              0,
            ];
          }
          // Apply the transform to the export map context
          CanvasRenderingContext2D.prototype.setTransform.apply(
              mapContext,
              matrix
          );
          const backgroundColor = canvas.parentNode.style.backgroundColor;
          if (backgroundColor) {
            mapContext.fillStyle = backgroundColor;
            mapContext.fillRect(0, 0, canvas.width, canvas.height);
          }
          mapContext.drawImage(canvas, 0, 0);
        }
      }
  );
  mapContext.globalAlpha = 1;
  mapContext.setTransform(1, 0, 0, 1, 0, 0);
  return mapCanvas;
}


export const log = (msg) => {
  console.log(msg);
  window['layman_logs'].push(msg);
}