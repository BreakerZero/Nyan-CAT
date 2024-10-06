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
const cloneCursor = document.getElementById('cloneCursor');
let radius = parseInt(localStorage.getItem('radius')) || 15; // Récupérer la valeur du local storage ou 15 par défaut
let clonePt = null;
let targetPt = null;
let imageHistory = [];
let cloneStampActive = false;
let currentTextBlock = null;
let isDragging = false;
let isResizing = false;
let offsetX, offsetY;

document.getElementById('diameterRange').value = radius;
document.getElementById('diameterValue').textContent = radius;

function saveState() {
    imageHistory.push(canvas.toDataURL('image/jpeg'));
}

function restoreState() {
    if (imageHistory.length > 0) {
        const imgData = imageHistory[imageHistory.length - 1];
        imageHistory.pop();
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
    button.style.backgroundColor = cloneStampActive ? '#ffffff' : '';
    document.getElementById('diameterControls').classList.toggle('hidden', !cloneStampActive);
    cloneCursor.style.display = cloneStampActive ? 'block' : 'none';
});

document.getElementById('diameterRange').addEventListener('input', (e) => {
    radius = parseInt(e.target.value);
    document.getElementById('diameterValue').textContent = radius;
    localStorage.setItem('radius', radius);
    updateCloneCursor();
});

canvas.addEventListener('mousemove', (e) => {
    if (!cloneStampActive) return;
    const canvasRect = canvas.getBoundingClientRect();
    const x = e.clientX - canvasRect.left + (document.getElementById('diameterRange').valueAsNumber/2);
    const y = e.clientY - canvasRect.top + (document.getElementById('diameterRange').valueAsNumber/1.5) + document.getElementById('ImageTranslatedLabel').getBoundingClientRect().height + document.getElementById('image-toolbar').getBoundingClientRect().height;

    cloneCursor.style.left = `${x - radius}px`;
    cloneCursor.style.top = `${y - radius}px`;
});

function updateCloneCursor() {
    cloneCursor.style.width = `${radius}px`;
    cloneCursor.style.height = `${radius}px`;
    cloneCursor.style.borderRadius = `${radius}px`;
}

// Initial call to set the cursor size
updateCloneCursor();

function addTextBlock() {
    const textBlock = document.createElement('div');
    textBlock.contentEditable = true;
    textBlock.style.position = 'absolute';
    textBlock.style.border = '1px solid black';
    textBlock.style.padding = '5px';
    textBlock.style.minWidth = '50px';
    textBlock.style.minHeight = '20px';
    textBlock.style.backgroundColor = 'transparent'; // Make background transparent
    textBlock.style.zIndex = '1000';
    textBlock.classList.add('text-block');

    // Position the text block initially inside the canvas
    const canvasRect = canvas.getBoundingClientRect();
    const initialX = canvasRect.left; // Initial offset from the left of the canvas
    const initialY = canvasRect.top + window.scrollY; // Initial offset from the top of the canvas, adjusted for scroll
    textBlock.style.left = `${initialX}px`;
    textBlock.style.top = `${initialY}px`;

    document.body.appendChild(textBlock); // Append to body

    // Use Interact.js for drag and resize
    interact(textBlock)
        .draggable({
            onmove: dragMoveListener,
            restrict: {
                restriction: canvas,
                elementRect: { top: 0, left: 0, bottom: 1, right: 1 }
            }
        })
        .resizable({
            edges: { left: true, right: true, bottom: true, top: true },
            restrictEdges: {
                outer: canvas,
                endOnly: true,
            },
            restrictSize: {
                min: { width: 50, height: 20 }
            },
            inertia: true
        })
        .on('resizemove', function(event) {
            const target = event.target;
            let x = (parseFloat(target.getAttribute('data-x')) || 0);
            let y = (parseFloat(target.getAttribute('data-y')) || 0);

            // Update the element's style
            target.style.width = event.rect.width + 'px';
            target.style.height = event.rect.height + 'px';

            // Translate when resizing from top or left edges
            x += event.deltaRect.left;
            y += event.deltaRect.top;

            target.style.transform = `translate(${x}px, ${y}px)`;

            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
        });
}

function dragMoveListener(event) {
    const target = event.target;
    let x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

    // Restrict movement within canvas bounds
    const canvasRect = canvas.getBoundingClientRect();
    const textBlockRect = target.getBoundingClientRect();

    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x + textBlockRect.width > canvasRect.width) x = canvasRect.width - textBlockRect.width;
    if (y + textBlockRect.height > canvasRect.height) y = canvasRect.height - textBlockRect.height;

    target.style.transform = `translate(${x}px, ${y}px)`;

    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
}

// Add text block on button click
document.getElementById('addTextButton').addEventListener('click', (e) => {
    e.preventDefault();
    addTextBlock();
});

document.getElementById('ValidationModifiedImgButton').addEventListener('click', async (e) => {
    e.preventDefault();

// Récupérer l'image du canvas en base64
    const canvas = document.getElementById('translatedImageCanvas');
    const imageBase64 = canvas.toDataURL('image/png');
    const section = document.getElementById("sectionnumber").value

    // Calculer les dimensions réelles du canvas et les dimensions affichées
    const realWidth = canvas.width;
    const realHeight = canvas.height;
    const displayedWidth = canvas.getBoundingClientRect().width;
    const displayedHeight = canvas.getBoundingClientRect().height;

    // Calculer le facteur d'échelle pour les positions et tailles des blocs de texte
    const scaleX = realWidth / displayedWidth;
    const scaleY = realHeight / displayedHeight;

    // Récupérer les positions et dimensions des blocs de texte
    const textBlocks = document.querySelectorAll('.text-block');
    const textData = [];

    textBlocks.forEach((block) => {
        const rect = block.getBoundingClientRect();
        const parentRect = canvas.getBoundingClientRect(); // Référencer par rapport au canvas
        const relativeX = (rect.left - parentRect.left) * scaleX;
        const relativeY = (rect.top - parentRect.top) * scaleY;
        const width = rect.width * scaleX;
        const height = rect.height * scaleY;
        const sizefont = parseFloat(window.getComputedStyle(block, null).getPropertyValue('font-size')) * scaleY;

        textData.push({
            content: block.innerText,
            x: relativeX,
            y: relativeY,
            width: width,
            height: height,
            sizefont: sizefont

        });
    });

    const editorContent = document.getElementsByClassName("ql-editor")[1].innerHTML.trim();
    let imgIsBefore = false;
    if (editorContent.startsWith('<img')) {
        imgIsBefore = true;
    }

    // Envoyer les données au backend
    try {
        const response = await fetch('/saveimg/' + id, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                textBlocks: textData,
                section : section,
                imgIsBefore: imgIsBefore,
                image: imageBase64
            })
        });

        if (response.ok) {
            alert('L\'image et les textes ont été sauvegardés avec succès.');
        } else {
            alert('Erreur lors de la sauvegarde. Veuillez réessayer.');
        }
    } catch (error) {
        console.error('Erreur lors de l\'envoi des données :', error);
    }
});
