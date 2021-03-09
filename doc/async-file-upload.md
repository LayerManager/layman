# Asynchronous file upload

In case of [POST Workspace Layers](rest.md#post-workspace-layers) and [PATCH Workspace Layer](rest.md#patch-workspace-layer), it is possible to upload data files asynchronously, which is suitable for large files. Let's demonstrate how it can be implemented on client side.

## HTML
You need some HTML form for user to choose files he wants to publish and fill some additional parametes:
```html
<form id="post-workspace-layers-form" >
  Vector data file:
  <input name="file" type="file" multiple />

  Layer name:
  <input name="name" type="text" />

  Layer title:
  <input name="title" type="text" />

  Layer description:
  <input name="description" type="text" />

  CRS:
  <input name="crs" type="text" />

  Style file:
  <input name="style" type="file" />

  <button type="submit">Submit</button>
</form>
```

Now, if you add `target="/rest/workspaces/some_workspace_name/layers" method="POST" enctype="multipart/form-data"` to the `form` element and let user click on Submit button, the browser will send everything to server **synchronously**. To do it **asynchronously**, you need to add some extra logic. 

## JavaScript

Brief overview:
- before [POST Workspace Layers](rest.md#post-workspace-layers) request is sent to the server, check file sizes and decide if to make sync or async file upload
- if async, switch from files to file names and save files for later async upload
- send [POST Workspace Layers](rest.md#post-workspace-layers) request using AJAX
- if async, read server response to setup [Resumable.js](http://www.resumablejs.com/) correctly, and start async upload of files

Example:
```js
import fetch from 'unfetch'; // https://github.com/developit/unfetch
import Resumable from "resumablejs"; // https://github.com/23/resumable.js

// can we use Resumable.js (= is File API supported) ?
const RESUMABLE_ENABLED = (new Resumable()).support;

// file size limit over which we prefer asynchronous upload
const PREFER_RESUMABLE_SIZE_LIMIT = 10 * 1024 * 1024; // 10 MB

const onFormSubmit = (event) => {
  // prevent immediate synchronous upload
  event.preventDefault();

  // but assume synchronous upload by default
  let async_upload = false;
  let files_to_async_upload = [];

  if (RESUMABLE_ENABLED) {
    // let's find out size of chosen files
    const form_data = new FormData(document.getElementById("post-workspace-layers-form"));
    const sum_file_size = form_data.getAll("file") // all files in "file" input
        .filter(f => f.name) // ignore files without name
        .reduce((prev, f) => prev + f.size, 0);

    // sync, or async ?
    async_upload = sum_file_size >= PREFER_RESUMABLE_SIZE_LIMIT;

    if (async_upload) {
      // save files for later upload
      const files = form_data.getAll('file').filter(f => f.name);
      files_to_async_upload.push(...files);
      // switch from files to file names in form data
      const file_names = files.map(f => f.name);
      form_data.delete('file');
      file_names.forEach(fn => form_data.append('file', fn));
    }
  }

  // send POST Workspace Layers request with form data
  fetch('/rest/workspaces/some_workspace_name/layers', {
    method: 'POST',
    body: form_data,
  }).then(r => {
    if (r.ok) {
      return JSON.parse(r.text());
    } else {
      throw new Error('Something goes wrong!');
    }
  }).then((resp_json) => {

    if (async_upload) {
      // let's prepare async upload

      // compare user-selected files to upload with server response,
      // leaving only files accepted by server
      files_to_async_upload = files_to_async_upload.filter(file_to_upload =>
          !!resp_json[0]['files_to_upload'].find(
              expected_file => file_to_upload.name === expected_file.file
          )
      );

      // find out layer name
      const layername = resp_json[0]['name'];

      // set up resumable.js instance
      const resumable = new Resumable({
        target: `/rest/workspaces/some_workspace_name/layers/${layername}/chunk`,
        query: {
          'layman_original_parameter': 'file'
        },
        // With testChunks=true, Resumable.js can check
        // which chunks are already uploaded on the server
        // and upload only the remaining ones.
        // It's a good choice when you previously uploaded same files,
        // but upload was not successful (e.g. because of connection failure).
        // Notice that testChunks=true will produce some GET requests with 404.
        // It's expected behaviour. If you don't like it, set testChunks to false.
        testChunks: true,
      });

      // set up some listeners
      resumable.on('progress', () => {
        console.log(`${Math.ceil(resumable.progress()*100)} % uploaded.`);
      });
      resumable.on('error', (message, file) => {
        console.error(message, file);
        throw new Error(`Something goes wrong during async upload!`);
      });
      resumable.on('complete', () => {
        console.log(`Async upload finished successfully!`);
      });
      resumable.on('filesAdded', (files) => {
        console.log(`${files.length} files added to Resumable.js, starting async upload.`);
        resumable.upload();
      });

      // add files to Resumable.js, it will fire 'filesAdded' event
      resumable.addFiles(files_to_async_upload.map(fo => fo.file));
    }
  });
};

// listen for user
document.getElementById("post-workspace-layers-form").addEventListener("submit", onFormSubmit);
```

