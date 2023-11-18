
class Page{
	constructor(){
		this.container = byId('content_container')
		this.type = null;
		this.handler = null;

		this.dir_tree = document.getElementById("dir-tree")

		this.dir_tree.scrollLeft = this.dir_tree.scrollWidth;
		// convert scroll to horizontal
		this.dir_tree.onwheel = function(event) {
			event.preventDefault();
			// scroll to left
			event.target.scrollBy({
				top: 0,
				left: event.deltaY,
				behavior: 'smooth'
			})
			event.deltaY < 0;
		}

		this.initialize()
	}

	get_type(){
		const url = tools.add_query_here('type', '');
		return fetch(url)
					.then(data => {return data.text()})
	}

	hide_all(){
		fm_page.hide()
		video_page.hide()
		admin_page.hide()
	}

	clear(){
		this.handler.clear()
	}

	async initialize(){
		/*for(let t=3; t>0; t--){
			console.log("Loading page in " + t)
			await tools.sleep (1000)
		}*/
		this.container.style.display = "none"
		this.hide_all()
		this.update_displaypath()

		this.type = await this.get_type()
		var type = this.type

		var old_handler = this.handler

		this.handler = null


		if (type == 'dir') {
			this.handler = fm_page;
		} else if (type == 'vid') {
			this.handler = video_page;
		} else if (type == "admin") {
			this.handler = admin_page;
		}

		if (this.handler){
			this.handler.initialize()
			this.handler.show()
		} else {
			popup_msg.createPopup("This type of page is not ready yet")
			popup_msg.show()

			this.handler = old_handler;
		}


		this.container.style.display = "block"

	}

	on_action_button() {
		this.handler.on_action_button()
	}

	set_title(title) {
		window.document.title = title;
	}

	set_diplaypath(displaypath) {
		this.dir_tree.innerHTML = displaypath;
	}

	update_displaypath() {
		const path = window.location.pathname;
		const dirs = path.replace(/\/{2,}/g, "/").split('/');
		const urls = ['/'];
		const names = ['&#127968; HOME'];
		const r = [];

		for (let i = 1; i < dirs.length - 1; i++) {
			const dir = dirs[i];
			urls.push(urls[i - 1] + encodeURIComponent(dir).replace(/'/g, "%27").replace(/"/g, "%22") + (dir.endsWith('/') ? '' : '/'));
			names.push(dir);
		}

		for (let i = 0; i < names.length; i++) {
			const tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>";
			r.push(tag);
		}

		this.set_diplaypath(r.join('<span class="dir_arrow">&#10151;</span>'));
	}

}

const page = new Page()
