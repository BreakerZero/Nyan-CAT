function checkForImageInEditor(editorElement) {
    var images = editorElement.getElementsByTagName('img');
    return images.length > 0 ? images[0] : null;
}
function loadCanvasWithImage(imgElement, canvasId) {
    var canvas = document.getElementById(canvasId);
    var ctx = canvas.getContext("2d");

    // Charger l'image dans le canvas
    var image = new Image();
    image.onload = function() {
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
    };
    image.src = imgElement.src;

    // Rendre le canvas visible
    canvas.style.display = "block";
}