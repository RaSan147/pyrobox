class Admin_page {
	constructor(){
		this.my_part = byId("admin_page")
	}

	initialize(){
		this.show()
	}

	show(){
		this.my_part.classList.add("active");
		updater.check_update();
		admin_tools.get_users();
	}

	hide(){
		this.my_part.classList.remove("active");
	}

	on_action_button() {
		// this.handler.on_action_button()
	}

	clear() {
		var table = byClass("users_list")[0]
		var rows = table.rows.length
		for (var i = 1; i < rows; i++) {
			table.deleteRow(1)
		}
	}
}

var admin_page = new Admin_page()


class Updater{
	async check_update() {
		fetch('/?update')
		.then(response => {
			// console.log(response);
			return response.json()
		}).then(data => {
			if (data.update_available) {
				byId("update_text").innerText = "Update Available! 🎉 Latest Version: " + data.latest_version ;
				byId("update_text").style.backgroundColor = "#00cc0033";

				byId("run_update").style.display = "block";
			} else {
				byId("update_text").innerText = "No Update Available";
				byId("update_text").style.backgroundColor = "#888";
			}
		})
		.catch(async err => {
			byId("update_text").innerText = "Update Error: " + "Invalid Response";
			byId("update_text").style.backgroundColor = "#CC000033";
		});
	}

	// run_update() {
	// 	byId("update_text").innerText = "Updating...";
	// 	fetch('/?update_now')
	// 	.then(response => response.json())
	// 	.then(data => {
	// 		if (data.status) {
	// 			byId("update_text").innerHTML = data.message;
	// 			byId("update_text").style.backgroundColor = "green";

	// 		} else {
	// 			byId("update_text").innerHTML = data.message;
	// 			byId("update_text").style.backgroundColor = "#bbb";
	// 		}
	// 	})
	// 	.catch(err => {
	// 		byId("update_text").innerText = "Update Error: " + "Invalid Response";
	// 		byId("update_text").style.backgroundColor = "#CC000033";
	// 	})


	// 	byId("run_update").style.display = "none";
	// }

}

var updater = new Updater();



class Admin_tools {
	constructor(){
		this.user_list = [];
	}

	async get_users() {
		fetch('/?get_users')
		.then(response => response.json())
		.then(data => {
			this.user_list = data;
			this.display_users();
		})
		.catch(err => {
			console.log(err);
		})
	}

	display_users() {
		var table = byClass("users_list")[0];
		var rows = table.rows.length;
		for (var i = 1; i < rows; i++) {
			table.deleteRow(1);
		}

		for (i = 0; i < this.user_list.length; i++) {
			var row = table.insertRow(-1);
			row.innerHTML = "<td>" + this.user_list[i] + "</td><td><div class='pagination' onclick='admin_tools.manage_user(" + i +
				")'>Manage</div></td></td><td>";
		}
	}

	show_perms(index) {

	}

	manage_user(index) {
		var username = this.user_list[index];


		const client_page_html = `
<form action="" method="post" class="perm_checker">
	<h2>Update Permissions</h2>
	<table>
		<tr>
			<td>View</td>
			<td><input type="checkbox" name="VIEW" value="0" id="view"></td>
		</tr>
		<tr>
			<td>Download</td>
			<td><input type="checkbox" name="DOWNLOAD" value="1" id="download"></td>
		</tr>
		<tr>
			<td>Modify</td>
			<td><input type="checkbox" name="MODIFY" value="2" id="modify"></td>
		</tr>
		<tr>
			<td>Delete</td>
			<td><input type="checkbox" name="DELETE" value="3" id="delete"></td>
		</tr>
		<tr>
			<td>Upload</td>
			<td><input type="checkbox" name="UPLOAD" value="4" id="upload"></td>
		</tr>
		<tr>
			<td>Zip</td>
			<td><input type="checkbox" name="ZIP" value="5" id="zip"></td>
		</tr>
		<tr>
			<td>Admin</td>
			<td><input type="checkbox" name="ADMIN" value="6" id="admin"></td>
		</tr>
	</table>

	<div class="submit_parent">
		<input type="submit" name="submit" value="Submit" id="submit">
	</div>
	
</form>

<br>
<div class='pagination' onclick='admin_tools.delete_user(" + i +")'
	style="margin: 0 auto;">Delete User</div>

<!-- 
on submit, get all the values and put them in a dict object
if admin is checked, all other values are checked -->


<!-- make the table and input look modern 
keep the submit button in center, modernize the button UI-->
<style>
	.perm_checker table {
		border-collapse: collapse;
		width: 100%;
		color: #afafaf;
		font-family: monospace;
		font-size: 25px;
		text-align: left;
	}
	.perm_checker tr:nth-child(even) {background-color: #4d4d4d}

	.perm_checker td:nth-child(1){
		text-align: left;
		width: calc(100% - 50px);
	}

	.perm_checker td:nth-child(2){
		text-align: center;
		width: 50px;
	}


	.perm_checker input[type=checkbox] {
		-moz-appearance:none;
		-webkit-appearance:none;
		-o-appearance:none;
		outline: none;
		content: none;	
	}

	.perm_checker input[type=checkbox]:before {
		content: "✅";
		font-size: 17px;
		color: transparent !important;
		background: #636363;
		display: block;
		width: 17px;
		height: 17px;
		border: 1px solid black;
	}

	.perm_checker input[type=checkbox]:checked:before {
		color: black !important;
	}

	.perm_checker input[type=submit] {
		background-color: #444;
		color: white;
		font-family: monospace;
		font-size: 25px;
		text-align: center;
		border: none;
		width: 60%;
		padding: 15px 32px;
		text-decoration: none;
		display: inline-block;
		margin: 4px 2px;
		cursor: pointer;

		border-radius: 2px;
		box-shadow: 5px 5px 0 0 #1abeff;
	}

	.perm_checker input[type=submit]:hover {
		background-color: #333;
		box-shadow: 3px 3px 0 0 #1abeff;
	}

	.perm_checker .submit_parent {
		display: flex;
		justify-content: center;
	}

</style>
		
		`

		var client_page_script = `
{
	var view = document.getElementById("view");
	var download = document.getElementById("download");
	var modify = document.getElementById("modify");
	var delete_ = document.getElementById("delete");
	var upload = document.getElementById("upload");
	var zip = document.getElementById("zip");
	var admin = document.getElementById("admin");

	var submit = document.getElementById("submit");

	var username = "` + username + `";
	var _user = new User();
	fetch('/?get_user_perm&username=' + username)
	.then(response => response.json())
	.then(data => {
		if (data.status) {
			_user.permissions_code = data.permissions_code;
			var perms = _user.extract_permissions();

			view.checked = perms["VIEW"];
			download.checked = perms["DOWNLOAD"];
			modify.checked = perms["MODIFY"];
			delete_.checked = perms["DELETE"];
			upload.checked = perms["UPLOAD"];
			zip.checked = perms["ZIP"];
			admin.checked = perms["ADMIN"];
		} else {
			popup_msg.createPopup(data["message"]);
			popup_msg.open_popup();
		}
	})


	submit.onclick = function(e) {
		e.preventDefault();
		var dict = {};
		dict["VIEW"] = view.checked;
		dict["DOWNLOAD"] = download.checked;
		dict["MODIFY"] = modify.checked;
		dict["DELETE"] = delete_.checked;
		dict["UPLOAD"] = upload.checked;
		dict["ZIP"] = zip.checked;
		dict["ADMIN"] = admin.checked;

		
		_user.permissions = dict;
		var perms = _user.pack_permissions();
		
		fetch('/?update_user_perm&username=' + username + "&perms=" + perms)
		.then(response => response.json())
		.then(data => {
			popup_msg.createPopup(data["status"], data["message"]);
			popup_msg.open_popup();
		})
		.catch(err => {
			console.log(err);
		})
	}
	

	admin.onclick = function() {
		if (admin.checked) {
			view.checked = true;
			download.checked = true;
			modify.checked = true;
			delete_.checked = true;
			upload.checked = true;
			zip.checked = true;
		}
	}

}
		`		


		popup_msg.createPopup(username + " Options", client_page_html, true, null_func, client_page_script);

		popup_msg.open_popup()
		

	}

	delete_user(index) {
		var username = this.user_list[index];
		r_u_sure({y:()=>{
			fetch('/?delete_user=' + username)
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data);
				this.get_users();
				popup_msg.open_popup();
			})
			.catch(err => {
				console.log(err);
			})
		}});
	}

	request_reload() {
		r_u_sure({y:()=>{
			fetch('/?reload')
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data)
				popup_msg.open_popup();
			})

		}});
	}

	request_shutdown() {
		r_u_sure({y:()=>{
			fetch('/?shutdown')
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data)
				popup_msg.open_popup();
			})

		}});
	}
}

var admin_tools = new Admin_tools();


