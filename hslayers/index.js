// import 'ol/ol.css';
import {json_to_map} from './src/map';

const map_def_url = 'https://raw.githubusercontent.com/jirik/gspld/1252fad2677f55182478c2206f47fbacb922fb97/sample/layman.map/full.json';


const main = async () => {

  const map_json = await fetch(map_def_url)
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

  ol_map.on('rendercomplete', () => {
    console.log('rendercomplete');
  });

};

main();