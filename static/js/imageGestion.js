function checkForImageInEditor(editorElement) {
    var images = editorElement.getElementsByTagName('img');
    return images.length > 0 ? images[0] : null;
}

function loadCanvasWithImage(imgElement, canvasId) {
    var canvas = document.getElementById(canvasId);
    var ctx = canvas.getContext("2d");

    var image = new Image();
    image.onload = function() {
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
    };
    image.src = imgElement.src;

    canvas.style.display = "block";
}

const canvas = document.getElementById('translatedImageCanvas');
const ctx = canvas.getContext('2d');
let radius = parseInt(localStorage.getItem('radius')) || 15; // Récupérer la valeur du local storage ou 15 par défaut
let clonePt = null;
let targetPt = null;
let imageHistory = [];
let cloneStampActive = false;

document.getElementById('diameterRange').value = radius;
document.getElementById('diameterValue').textContent = radius;

function saveState() {
    imageHistory.push(canvas.toDataURL());
}

function restoreState() {
    if (imageHistory.length > 1) {
        imageHistory.pop();
        const imgData = imageHistory[imageHistory.length - 1];
        const img = new Image();
        img.src = imgData;
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
    }
}

canvas.addEventListener('mousedown', (e) => {
    if (!cloneStampActive) return;

    const canvasRect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / canvasRect.width;
    const scaleY = canvas.height / canvasRect.height;

    const x = (e.clientX - canvasRect.left) * scaleX;
    const y = (e.clientY - canvasRect.top) * scaleY;
    if (e.button === 2) {
        clonePt = { x, y };
    } else if (e.button === 0 && clonePt) {
        targetPt = { x, y };
        saveState();
        applyClone(clonePt, targetPt, radius);
    }
});

function applyClone(clonePt, targetPt, radius) {
    const imgData = canvas.toDataURL('image/jpeg').split(',')[1];

    fetch('/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            image: imgData,
            clone_pt: clonePt,
            target_pt: targetPt,
            radius: parseInt(radius)
        })
    })
    .then(response => response.json())
    .then(data => {
        const image = new Image();
        image.src = 'data:image/jpeg;base64,' + data.image;
        image.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(image, 0, 0);
        };
    });
}

canvas.addEventListener('contextmenu', (e) => e.preventDefault());

document.getElementById('undoButton').addEventListener('click', (e) => {
    e.preventDefault();
    restoreState();
});

document.getElementById('cloneStampButton').addEventListener('click', (e) => {
    e.preventDefault();
    cloneStampActive = !cloneStampActive;
    const button = document.getElementById('cloneStampButton');
    button.classList.toggle('is-active', cloneStampActive);
    button.style.backgroundColor = cloneStampActive ? 'white' : '';
    document.getElementById('diameterControls').classList.toggle('hidden', !cloneStampActive);
});

document.getElementById('diameterRange').addEventListener('input', (e) => {
    radius = parseInt(e.target.value);
    document.getElementById('diameterValue').textContent = radius;
    localStorage.setItem('radius', radius);
});
