var toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike', 'clean'],
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],      // toggled buttons
  [{ 'indent': '-1'}, { 'indent': '+1' }],         // outdent/indent
  [{ 'color': [] }],          // dropdown with defaults from theme
  [{ 'align': [] }],
];
var quill = new Quill('#editorjs', {
  modules: {
    toolbar: toolbarOptions,
    clipboard: {
      newLines: false
    },
    keyboard: {
      bindings: {
      enter: {
        key: 13,
        handler: function() {
          return false;
        }
      }
    }
  }
  },
  theme: 'snow'
});
quill.root.setAttribute('spellcheck', false)
var disabledquill = new Quill('#disablededitorjs', {
  modules: {
    toolbar: toolbarOptions
  },
  readOnly: true,
  theme: 'snow'
});