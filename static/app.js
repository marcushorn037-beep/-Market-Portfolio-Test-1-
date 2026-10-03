document.addEventListener('DOMContentLoaded', function () {
  const dateNode = document.getElementById('currentDate');
  if (dateNode) {
    const today = new Date();
    dateNode.textContent = today.toLocaleDateString('en-CA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
});
