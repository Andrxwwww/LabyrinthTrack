<?php
// Connect to the remote database
$host = '194.210.86.10';
$db = 'maze';
$user = 'aluno';
$pass = 'aluno';

$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
    die("Erro na ligação: " . $conn->connect_error);
}

$playerId = intval($_GET['player'] ?? 15);
$query = "SELECT Room, score FROM roomsscore WHERE Player = ?";
$stmt = $conn->prepare($query);
$stmt->bind_param("i", $playerId);
$stmt->execute();
$result = $stmt->get_result();

$roomIDs = [];
$scores = [];

while ($row = $result->fetch_assoc()) {
    $roomIDs[] = "Room " . $row['Room'];
    $scores[] = $row['score'];
}

$conn->close();
?>
<!DOCTYPE html>
<html>
<head>
    <title>Score Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h2>Player <?= $playerId ?> Scores</h2>
    <canvas id="scoreChart" width="600" height="400"></canvas>
    <script>
        const ctx = document.getElementById('scoreChart').getContext('2d');
        const scoreChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: <?= json_encode($roomIDs) ?>,
                datasets: [{
                    label: 'Score',
                    data: <?= json_encode($scores) ?>,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)'
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
