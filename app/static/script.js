function test() {
	console.log('JS Loaded');
}

const canvas = document.getElementById('disp');
const context = canvas.getContext('2d');

canvas.width = 512;
canvas.height = 512;
context.lineWidth = 10;

var nodes = [];

function drawNode(node) {
	context.beginPath();
	context.fillStyle = node.fillStyle;
	context.arc(node.x, node.y, node.radius, 0, Math.PI * 2, true);
	context.strokeStyle = node.strokeStyle;
	context.stroke();
	context.fill();
}


function create_node(x, y) {
	let node = {
		x: x,
		y: y,
		radius: 2.5,
		fillStyle: '#777777',
		strokeStyle: '#ececec'
	};
	nodes.push(node);
	drawNode(node);
}

function create_edge(x1, y1, x2, y2) {
	context.beginPath();
	context.moveTo(x1, y1);
	context.lineTo(x2, y2);
	context.strokeStyle = '#cccccc';
	context.stroke();
}

canvas.onmousemove = function(e) {
	tooltip = document.getElementById("tt")
	var x = e.clientX
	var y = e.clientY
	tooltip.style.top = (y + 15) + 'px';
	tooltip.style.left = (x + 15) + 'px';
	pos = getMousePos(canvas, e)
	var inradius = {}
	let close;
    if (typeof hotspots !== 'undefined') {
	hotspots.forEach(function(item, index) {
		var dx = pos.x - item.x;
		var dy = pos.y - item.y;
		if (dx * dx + dy * dy < item.radius * item.radius) {
			tooltip.style.display = "block";
			tooltip.classList.remove("hide");
			tooltip.classList.add('show');
			document.getElementById("node_pos").innerText = `(${item.x.toFixed(2)}, ${item.y.toFixed(2)})`;
			document.getElementById("node_name").innerText = item.tip;
			inradius[index] = true;
		} else {
			inradius[index] = false;
		}
	});
	if (Object.values(inradius).every(
			value => value === false
		)) {
		tooltip.classList.remove("show");
		tooltip.classList.add('hide');
	}
    }
};


var hotspots;

function setHotSpot(list) {
	hotspots = []
	list.forEach(function(item, index) {
		hotspots.push({
			x: item[0],
			y: item[1],
			radius: 5,
			tip: item[2]
		});
	});
}


function getMousePos(canvas, evt) {
	var rect = canvas.getBoundingClientRect();
	return {
		x: evt.clientX - rect.left,
		y: evt.clientY - rect.top
	};
}