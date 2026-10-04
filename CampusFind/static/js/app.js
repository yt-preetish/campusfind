
document.addEventListener("DOMContentLoaded", () => {
  const dt = document.querySelector('input[type="datetime-local"]');
  if (dt && !dt.value) {
    const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    dt.value = d.toISOString().slice(0,16);
  }
  document.querySelectorAll(".flash").forEach(el => {
    setTimeout(()=>{el.style.opacity="0"; el.style.transition=".4s"; setTimeout(()=>el.remove(),400)}, 4500);
  });
});
