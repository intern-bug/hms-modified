const letterFloorMap = new Map()
letterFloorMap.set('G', 'Ground');
letterFloorMap.set('F', 'First');
letterFloorMap.set('S', 'Second');
letterFloorMap.set('T', 'Third');
letterFloorMap.set('FT', 'Fourth');

function loader(){
  var filled_count = 0;
  var partial_count = 0;
  var vacant_count = 0;

  document.querySelectorAll('.room-card').forEach((room_card) => {
    let room_str = room_card.innerHTML;
    let [floor, no] = room_str.split("-");
    no = parseInt(no);
    floor = letterFloorMap.get(floor);
    let room_students = roomdetails.filter(room => room.floor == floor && room.room_no == no);
    let count = room_students.length || 0;
    if (count == room_capacity) {
      filled_count += 1;
      room_card.classList.add('filled');
    } else if (0 < count && count < room_capacity) {
      room_card.classList.add("partial");
      partial_count += 1;
    } else if (count == 0) {
      vacant_count += 1;
    }

    $(room_card).hover(() => {
      const room_regd_nos = room_students.map(stud => stud.student.regd_no).join(", ");
      if (room_regd_nos.length > 0) {
        $(room_card).tooltip({title: room_regd_nos}).tooltip('show');
      }
    });

    const table = document.getElementById("table-container");
    room_card.addEventListener('click', function() {
      placeDetails(room_str, floor, no, room_students);
      if (table.classList.contains('d-none')) {
        table.classList.add('d-block');
        table.classList.remove('d-none');
      }  
      document.querySelector('#table-container table > tbody').scrollIntoView();
    });
  });

  document.getElementById('filled_room').innerHTML = filled_count;
  document.getElementById('partial_room').innerHTML = partial_count;
  document.getElementById('vacant_room').innerHTML = vacant_count;
  let floor = document.getElementById('floor').value.toLowerCase();
  floor = floor+"-con";
  document.getElementById(floor).style.display = "block";
}

window.load = loader()

function closeRoomTable() {
  table = document.getElementById("table-container");
  if (table.classList.contains('d-block')) {
    table.classList.remove('d-block');
    table.classList.add('d-none');
  }
}

function showFloor() {
  const floor = document.getElementById("floor").value.toLowerCase();
  const floor_id = floor+"-con";
  document.querySelectorAll(".floor-con").forEach(floor_con => floor_con.style.display = "none");
  document.getElementById(floor_id).style.display = "block";
}

function placeDetails(room_str, floor, no, room_students) {
  document.querySelector('#table-container h2#room').innerHTML = room_str;
  let tbody = document.querySelector('#table-container table > tbody');
  let room_type = {'1S':1, '2S':2, '4S':4}
  tbody.innerHTML = "";
  let bed_filled = [];
  room_students.forEach(room => {
    let row = document.createElement('tr');
    bed_filled.push(parseInt(room.bed))
    let regd_no_td = document.createElement('td');
    let roll_no_td = document.createElement('td');
    let name_td = document.createElement('td');
    let bed_td = document.createElement('td');
    let year_td = document.createElement('td');
    let branch_td = document.createElement('td');
    let phone_td = document.createElement('td');
    let email_td = document.createElement('td');
    regd_no_td.innerHTML = room.student.regd_no;
    roll_no_td.innerHTML = room.student.roll_no;
    name_td.innerHTML = room.student.name;
    bed_td.innerHTML = room.bed;
    year_td.innerHTML = room.student.year;
    branch_td.innerHTML = room.student.branch;
    phone_td.innerHTML = room.student.phone;
    email_td.innerHTML = room.student.email;
    let form_td = document.createElement('td');
    let form = document.createElement('form');
    form.method = "POST";
    let room_id_input = document.createElement('input'); 
    let remove_input = document.createElement('input'); 
    let download_input = document.createElement('input'); 
    let renew_input = document.createElement('input'); 
    room_id_input.type = 'hidden';
    room_id_input.name = 'roomdetail_id';
    room_id_input.value = room.id;
    remove_input.type = 'submit';
    remove_input.name = 'remove';
    remove_input.value = 'Remove';
    remove_input.className = 'btn btn-danger';
    remove_input.onclick = "return confirm('Are you sure?')";
    download_input.name = 'download';
    download_input.type = 'submit';
    download_input.value = 'Download';
    download_input.className = 'btn btn-primary';
    renew_input.type = 'button';
    renew_input.name = 'renew';
    renew_input.value = 'Renew';
    renew_input.className = 'btn btn-primary';
    renew_input.addEventListener('click', function () {
      renewRoomDetail(room, floor, no);
    })
    form.appendChild(room_id_input);
    form.appendChild(remove_input);
    form.appendChild(download_input);
    form.appendChild(renew_input);
    form_td.appendChild(form);
    row.appendChild(regd_no_td);
    row.appendChild(roll_no_td);
    row.appendChild(name_td);
    row.appendChild(bed_td);
    row.appendChild(year_td);
    row.appendChild(branch_td);
    row.appendChild(phone_td);
    row.appendChild(email_td);
    row.appendChild(form_td);
    // row.innerHTML = `
    //   <td>${room.student.regd_no}</td>\
    //   <td>${room.student.roll_no}</td>\
    //   <td>${room.student.name}</td>\
    //   <td>${room.bed}</td>\
    //   <td>${room.student.year}</td>\
    //   <td>${room.student.branch}</td>\
    //   <td>${room.student.phone}</td>\
    //   <td>${room.student.email}</td>\
    //   <td>\
    //     <form method="POST">
    //       <input type="hidden" name="roomdetail_id" value="${room.id}" />
    //       <input type='submit' name='remove' value='Remove' class='btn btn-danger' onclick="return confirm('Are you sure?')" />\
    //       <input type='submit' name='download' value='Download' class='btn btn-primary' />\
    //       <input type='button' name='renew' value='Renew' onclick=renewRoomDetail() class='btn btn-primary' />\
    //     </form>
    //   </td>`;
    tbody.appendChild(row);
  })
  bed_choices = ''
  for (let i=1; i<=room_type[current_block.room_type]; i++){
    if (bed_filled.includes(i)==false){
      bed_choices = bed_choices + `<option value=\'${i}\'>${i}</option>`
    }
  }
  if (room_students.length < room_capacity) {
    let row = document.createElement('tr');
    row.innerHTML = `
      <td colspan='10' class='text-center'>\
        <form method="POST">
          Add Student to room :\
          <input type='text' name='regd_no' class='ml-3' required> \
          Select Bed :\ 
          <select name='bed' class='ml-3' required>\
            <option value=''>----</option>
            ${bed_choices}\
          </select>\
          <input type='hidden' name='block_id' value='${current_block.id}' /> \
          <input type='hidden' name='floor' value='${floor}' /> \
          <input type='hidden' name='room_no' value='${no}' /> \
          <br>
          <br>
          Amount Paid : \
          <input type='number' name='amount_paid' class='ml-3' required>\
          Mode of Payment :\
          <select name='payment_mode' class='ml-3' required>\
            <option value=''>-----</option>
            <option value='sbi i-Collect'>sbi i-Collect</option>\
            <option value='NEFT'>NEFT</option>\
            <option value='Education Loan'>Education Loan</option>\
            <option value='Other'>Other</option>\
          </select>\
          Date of Payment:
          <input type='date' name='date_of_payment' required>
          <br>
          <br>
          <input type='submit' name='Add' value='Add' class='btn btn-primary ml-5'>\
        </form>
      </td>`;
    tbody.appendChild(row); 
  }
}

function renewRoomDetail(room, floor, no){
  let tbody = document.querySelector('#table-container table > tbody');
  tbody.deleteRow(-1);
  let row = document.createElement('tr');
    row.innerHTML = `
      <td colspan='10' class='text-center'>\
        <form method="POST">
          Add Student to room :\
          <input type='text' name='regd_no' value=${room.student.regd_no} class='ml-3' required> \
          Select Bed :\ 
          <select name='bed' class='ml-3' required>\
            <option value='${room.bed}'>${room.bed}</option>
          </select>\
          <input type='hidden' name='block_id' value='${current_block.id}' /> \
          <input type='hidden' name='roomdetail_id' value='${room.id}' /> \
          <input type='hidden' name='floor' value='${floor}' /> \
          <input type='hidden' name='room_no' value='${no}' /> \
          <br>
          <br>
          Amount Paid : \
          <input type='number' step=0.01 name='amount_paid' class='ml-3' required>\
          Mode of Payment :\
          <select name='payment_mode' class='ml-3' required>\
            <option value=''>-----</option>
            <option value='sbi i-Collect'>sbi i-Collect</option>\
            <option value='NEFT'>NEFT</option>\
            <option value='Education Loan'>Education Loan</option>\
            <option value='Other'>Other</option>\
          </select>\
          Date of Payment:
          <input type='date' name='date_of_payment' required>
          <br>
          <br>
          <input type='submit' name='renew' value='Renew' class='btn btn-primary ml-5'>\
        </form>
      </td>`;
    tbody.appendChild(row); 
}
