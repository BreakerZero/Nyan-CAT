 setInputFilter(document.getElementById("sectionnumber"), function(value) {return /^\d*$/.test(value);});
    function upsectionnumber(){
        stopSectionTimer();
        startSectionTimer();
        document.getElementById("sectionnumber").value = parseInt(document.getElementById("sectionnumber").value ) + 1;
        getRessourceProject(document.getElementById('sectionnumber').value);
    }
    function downsectionnumber(){
        stopSectionTimer();
        startSectionTimer();
        if (document.getElementById("sectionnumber").value != "0")
        document.getElementById("sectionnumber").value = parseInt(document.getElementById("sectionnumber").value ) - 1;
        getRessourceProject(document.getElementById('sectionnumber').value);
    }

    let startTime; // To track when the user started on a section
    let timeSpent = []; // Array to store time spent on each section
    function startSectionTimer() {
        startTime = new Date();
    }

    function stopSectionTimer() {
        if (startTime) {
            let endTime = new Date();
            let duration = (endTime - startTime) / 1000; // Duration in seconds
            timeSpent.push(duration);
            startTime = null;

            updateRemainingTime();
        }
    }

    function updateRemainingTime() {
        if (timeSpent.length === 0) return;

        // Calcul de la médiane
        let sortedTimes = [...timeSpent].sort((a, b) => a - b);
        let medianTime;
        if (sortedTimes.length % 2 === 0) {
            // Si le nombre est pair, moyenne des deux valeurs centrales
            medianTime = (sortedTimes[sortedTimes.length / 2 - 1] + sortedTimes[sortedTimes.length / 2]) / 2;
        } else {
            // Si le nombre est impair, on prend la valeur centrale
            medianTime = sortedTimes[Math.floor(sortedTimes.length / 2)];
        }

        // Calcul du nombre de sections restantes
        let remainingSections = parseFloat(document.getElementById("totalsection").textContent.replace(/^\D+/g, '')) - document.getElementById("sectionnumber").value;
        let estimatedTimeRemaining = medianTime * remainingSections;

        // Formatage du temps restant en heures, minutes, et secondes
        let hours = Math.floor(estimatedTimeRemaining / 3600);
        let minutes = Math.floor((estimatedTimeRemaining % 3600) / 60);
        let seconds = Math.floor(estimatedTimeRemaining % 60);

        document.getElementById("remaining-time").innerText =
            `Temps restant estimé : ${hours}h ${minutes.toString().padStart(2, '0')}m ${seconds.toString().padStart(2, '0')}s`;
    }

    startSectionTimer();