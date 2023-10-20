
class Admin_page {
	constructor(){
		this.my_part = byId("admin_page")
	}

	initialize(){
		this.show()
	}

	show(){
		byId("admin_page").style.display = "block";
	}

	hide(){
		byId("admin_page").style.display = "none";
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

const admin_page = new Admin_page()


class Updater{
	async check_update() {
		fetch('/?update')
		.then(response => {
			console.log(response);
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
updater.check_update();


class Admin_tools {
	constructor(){
		this.user_list = [];
		this.get_users();
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
			row.innerHTML = "<td>" + this.user_list[i] + "</td><td><div class='pagination' onclick='admin_tools.update_user_perm(" + i + 
				")'>Permissions</div></td></td><td><div class='pagination' onclick='admin_tools.delete_user(" + i + 
					")'>Delete</div></td>";
		}
	}

	show_perms(index) {
		
	}

	update_user_perm(index) {
		var username = this.user_list[index];
		var perms = prompt("Enter new permissions for " + username + ":", "admin");
		if (perms != null) {
			fetch('/?update_user_perm=' + username + "&perms=" + perms)
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data);
				this.get_users();
			})
			.catch(err => {
				console.log(err);
			})
		}
	}

	delete_user(index) {
		var username = this.user_list[index];
		r_u_sure({y:()=>{
			fetch('/?delete_user=' + username)
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data);
				this.get_users();
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
			})
	
		}});
	}
	
	request_shutdown() {
		r_u_sure({y:()=>{
			fetch('/?shutdown')
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data)
			})
	
		}});
	}
}

var admin_tools = new Admin_tools();


