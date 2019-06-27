// import 'ol/ol.css';
import {json_to_map, adjust_map_url} from './src/map';
import { saveAs } from 'file-saver';

// const map_def_url = 'https://raw.githubusercontent.com/jirik/gspld/1252fad2677f55182478c2206f47fbacb922fb97/sample/layman.map/full.json';

const url_params = new URLSearchParams(window.location.search);
const map_def_url = url_params.get('map_def_url');
const file_name = url_params.get('file_name');


const main = async () => {
  if(!map_def_url) {
    console.error(`Query does not contain map_def_url parameter`);
    return;
  }

  const map_json = await fetch(adjust_map_url(map_def_url))
      .then(response => {
            if (response.status !== 200) {
              throw Error(`Cannot read composition ${map_def_url}`);
            }
            return response.json();
          }
      );
  const ol_map = json_to_map({
    map_json,
  });

  ol_map.once('rendercomplete', (event) => {
    // console.log('rendercomplete');
    const canvas = event.context.canvas;
    console.log('dataurl', canvas.toDataURL());
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