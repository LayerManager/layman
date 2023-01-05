// import 'ol/ol.css';
import {json_to_map, adjust_map_url, map_to_canvas} from './src/map';
import { saveAs } from 'file-saver';

// const map_def_url = 'https://raw.githubusercontent.com/LayerManager/layman/1252fad2677f55182478c2206f47fbacb922fb97/sample/layman.map/full.json';

const url_params = new URLSearchParams(window.location.search);
const get_url_param = (param_name) => {
  return url_params.get(param_name) ? decodeURIComponent(url_params.get(param_name)) : null;
}

const gs_url = get_url_param('gs_url');
const gs_public_url = get_url_param('gs_public_url');
const map_def_url = get_url_param('map_def_url');
const proxy_header = url_params.get('proxy_header') || null;
const editor = url_params.get('editor') || null;
const file_name = url_params.get('file_name') || null;


const main = async () => {
  if(!map_def_url) {
    console.error(`Query does not contain map_def_url parameter`);
    return;
  }

  const headers = {};
  if(proxy_header && editor) {
    headers[proxy_header] = editor;
  }
  const map_json = await fetch(
      adjust_map_url(map_def_url),
      {
        headers,
      },
  ).then(response => {
            if (response.status !== 200) {
              throw Error(`Cannot read composition ${map_def_url}`);
            }
            return response.json();
          }
      );
  const ol_map = json_to_map({
    map_json,
    gs_url,
    gs_public_url,
    headers,
  });

  ol_map.once('rendercomplete', (event) => {
    // console.log('rendercomplete');
    const canvas = map_to_canvas(ol_map);
    window['canvas_data_url'] = canvas.toDataURL();
    if(file_name) {
      if (navigator.msSaveBlob) {
        navigator.msSaveBlob(canvas.msToBlob(), file_name);
      } else {
        canvas.toBlob((blob) => {
          saveAs(blob, file_name);
        });
      }
    }
  });
  ol_map.renderSync();

};

main();
