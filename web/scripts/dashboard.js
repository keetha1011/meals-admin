function signout() {
  window.location.href = "sign-out";
}


const modal = document.getElementById("recipeInfo");
//const modal_bg = document.getElementsByClassName("bg")
const btn = document.getElementById("recipes");
const span = document.getElementsByClassName("close")[0];

btn.onclick = function () {
  modal.style.display = "block";
  //modal_bg.style.display = "flex";
  //modal.style.backgroundColor = "rgba(255,255,255,0.2)";
  //modal.style.backgroundBlendMode = "hard-light";
};

span.onclick = function () {
  modal.style.display = "none";
};

window.onclick = function (event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
};

function recipeUpdater() {
  console.log("Recipe Updated");
}