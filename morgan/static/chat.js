window.addEventListener("load", function() {
    window.scrollTo(0, document.body.scrollHeight);
});

function flag_popup(msg_id) {
    console.log("Flag popup");
    var dlg = $('[id="flag-modal"]');
    dlg[0].msg_flag = msg_id;
    dlg.modal('show');
}

function flag_submit() {
    var dlg = $('[id="flag-modal"]');
    msg_id = dlg[0].msg_flag;
    x = '[id="msg-'+(msg_id-1)+'"]';
    user_txt = $(x).find('.card-text').text();
    x = '[id="msg-'+msg_id+'"]';
    asst_txt = $(x).find('.card-text').text();
    x = '[id="flag_msg"]';
    flag_txt = $(x)[0].value; 
    
    // Create a new XMLHttpRequest object
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    var is_pending = false;
  
    // Define the URL you want to fetch data from
    var url = "/chat-flag-submit/";
  
    // Configure the AJAX request
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
  
    // Set up a callback function to handle the response
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200) {
        var responseData = xhr.response;
        console.log("Response data:", responseData);
        var x = "[id='flag-"+msg_id+"']";
        $(x).attr('disabled', 'disabled')
      } else if (xhr.readyState === 4 && xhr.status !== 200) {
        // An error occurred during the request
        console.error("Error fetching data. Status code:", xhr.status);
      }
    };
  
    // Send the AJAX request
    xhr.send(JSON.stringify({ "user_txt": user_txt, "asst_txt": asst_txt, "flag_txt": flag_txt }));
};
