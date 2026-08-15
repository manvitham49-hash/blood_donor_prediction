function predict() {
    const city = document.getElementById("city").value;
    const months = document.getElementById("months").value;
    const donations = document.getElementById("donations").value;
    const pints = document.getElementById("pints").value;
    const result = document.getElementById("result");

    if (city === "" || months === "" || donations === "" || pints === "") {
        result.innerHTML = "❌ Please fill all fields";
        result.style.color = "orange";
        return;
    }

    // TEMPORARY rule-based logic (will replace with ML later)
    if (donations >= 3 && months >= 6 && pints >= 2) {
        result.innerHTML = "🟢 Donor is AVAILABLE in " + city;
        result.style.color = "green";
    } else {
        result.innerHTML = "🔴 Donor is NOT AVAILABLE in " + city;
        result.style.color = "red";
    }
}
