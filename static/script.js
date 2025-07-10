const form = document.getElementById("match-setup-form");
const playerSection = document.getElementById("player-selection");
const teamASelect = document.getElementById("team_a");
const teamBSelect = document.getElementById("team_b");

form.addEventListener("submit", function (e) {
  e.preventDefault();
  const teamA = teamASelect.value.trim();
  const teamB = teamBSelect.value.trim();
  const venue = document.getElementById("venue").value.trim();
  document.getElementById("hidden-venue").value =
    document.getElementById("venue").value;

  if (teamA && teamB && venue && teamA !== teamB) {
    loadPlayerDropdownTable(teamA, teamB);
    playerSection.style.display = "block";
  }
});

teamASelect.addEventListener("change", updateDropdowns);
teamBSelect.addEventListener("change", updateDropdowns);

function updateDropdowns() {
  const selectedA = teamASelect.value;
  const selectedB = teamBSelect.value;

  [...teamASelect.options].forEach((opt) => (opt.disabled = false));
  [...teamBSelect.options].forEach((opt) => (opt.disabled = false));

  if (selectedA) {
    [...teamBSelect.options].forEach((opt) => {
      if (opt.value === selectedA) opt.disabled = true;
    });
  }

  if (selectedB) {
    [...teamASelect.options].forEach((opt) => {
      if (opt.value === selectedB) opt.disabled = true;
    });
  }
}

function loadPlayerDropdownTable(teamA, teamB) {
  Promise.all([
    fetch("/get_players", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team: teamA }),
    }).then((res) => res.json()),
    fetch("/get_players", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team: teamB }),
    }).then((res) => res.json()),
  ]).then(([playersA, playersB]) => {
    const tableBody = document.getElementById("player-table-body");
    tableBody.innerHTML = "";

    for (let i = 0; i < 11; i++) {
      const row = document.createElement("tr");
      
      row.innerHTML = `
        <td>
          <select class="team-a-select" onchange="handlePlayerChange(this, 'A', ${i}, '${teamA}')">
            <option value="">-- Select Player --</option>
            ${playersA
              .map((p) => `<option value="${p}">${p}</option>`)
              .join("")}
          </select>
          <div id="info-A-${i}">Credit: -- | Type: -- | Team: ${teamA}</div>
        </td>
        <td>
          <select class="team-b-select" onchange="handlePlayerChange(this, 'B', ${i}, '${teamB}')">
            <option value="">-- Select Player --</option>
            ${playersB
              .map((p) => `<option value="${p}">${p}</option>`)
              .join("")}
          </select>
          <div id="info-B-${i}">Credit: -- | Type: -- | Team: ${teamB}</div>
        </td>
      `;

      tableBody.appendChild(row);
    }

    document.querySelectorAll(".team-a-select").forEach((sel, i) => {
      if (sel.value) handlePlayerChange(sel, "A", i, teamA);
    });

    document.querySelectorAll(".team-b-select").forEach((sel, i) => {
      if (sel.value) handlePlayerChange(sel, "B", i, teamB);
    });
  });
}

function handlePlayerChange(select, teamLabel, index, teamName) {
  const allSelects = document.querySelectorAll(
    `.team-${teamLabel.toLowerCase()}-select`
  );
  const selected = new Set();

  allSelects.forEach((sel) => {
    if (sel.value) selected.add(sel.value);
  });

  allSelects.forEach((sel) => {
    Array.from(sel.options).forEach((opt) => {
      if (opt.value && opt.value !== sel.value) {
        opt.disabled = selected.has(opt.value);
      } else {
        opt.disabled = false;
      }
    });
  });

  getPlayerInfo(select, teamLabel, index, teamName);
}

function getPlayerInfo(select, teamLabel, index, teamName) {
  const player = select.value;
  if (!player) return;

  fetch("/get_player_info", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player: player, team: teamName }),
  })
    .then((res) => res.json())
    .then((info) => {
      document.getElementById(
        `info-${teamLabel}-${index}`
      ).innerHTML = `<span class="text-sm text-gray-700"> Credit: ${info.credit} | Type: ${info.type} | Team: ${info.team}</span>`;
    });
}

document
  .getElementById("generate-excel-btn")
  .addEventListener("click", function () {
    const selectedPlayers = {
      teamA: [],
      teamB: [],
      teamA_name: document.getElementById("team_a").value,
      teamB_name: document.getElementById("team_b").value,
    };

    document.querySelectorAll(".team-a-select").forEach((sel) => {
      if (sel.value) selectedPlayers.teamA.push(sel.value);
    });

    document.querySelectorAll(".team-b-select").forEach((sel) => {
      if (sel.value) selectedPlayers.teamB.push(sel.value);
    });

    if (
      selectedPlayers.teamA.length !== 11 ||
      selectedPlayers.teamB.length !== 11
    ) {
      alert("Please select 11 players from both teams.");
      return;
    }

    fetch("/generate_excel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(selectedPlayers),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          alert("Excel file generated successfully!");
          const predictBtn = document.getElementById("predict-btn");
          predictBtn.disabled = false; // ✅ enable the button
          predictBtn.style.display = "inline-block"; // ✅ ensure it's visible
        } else {
          alert("Error: " + data.message);
        }
      });
  });

document.getElementById("predict-btn").addEventListener("click", function () {
  window.location.href = "/predict";
});
