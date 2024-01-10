window.addEventListener("load", function() {
    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();
  
    // Define the URL you want to fetch data from
    var url = "/chat-check-status";
  
    // Configure the AJAX request
    xhr.open("GET", url, true);
  
    // Set up a callback function to handle the response
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        // The request was successful, and data is available in xhr.responseText
        var responseData = xhr.responseText;
  
        // You can process the responseData here as needed
        console.log("Response data:", responseData);
      } else if (xhr.readyState === 4 && xhr.status !== 200) {
        // An error occurred during the request
        console.error("Error fetching data. Status code:", xhr.status);
      }
    };
  
    // Send the AJAX request
    xhr.send();
  });
  