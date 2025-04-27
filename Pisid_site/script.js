document
  .getElementById("show-register")
  .addEventListener("click", function (e) {
    e.preventDefault();
    document.querySelector(".flip-card").classList.add("flipped");
  });

document.getElementById("show-login").addEventListener("click", function (e) {
  e.preventDefault();
  document.querySelector(".flip-card").classList.remove("flipped");
});
