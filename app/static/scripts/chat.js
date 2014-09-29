(function($,jQuery,window){
	
	var chatAPI = {

		connect : function(done) {

			var that = this;
			
			var room = $("#room-id").val();
			console.log('url',room)

			this.socket = io.connect('/' + $('.room-id').html());
			this.socket.on('connect', done);

			this.socket.on('message', function(message){
				if(that.onMessage){
					that.onMessage(message);
				}
			});
		},

		join : function(email, onJoin){
			this.socket.emit('join', email, onJoin);
		},

		sendMessage : function(message, onSent) {
			this.socket.emit('message', message, onSent);
		}

	};	

	var connectUser = function() {
		chatAPI.join($('.nickname').html(), function(joined, name){
			if(joined){
				console.log("You've joined Chat",name);
			}
		});
	}

	var bindUI = function(){

		$(".compose-message-form").find("[name='message']").on("keyup",function(e){
			e = e || event;
			if (e.keyCode === 13) {
				$(".compose-message-form").submit();
			}
			return true;
		});

		$(".compose-message-form").validate({
			submitHandler: function(form) {
				chatAPI.sendMessage($(form).find("[name='message']").val(), function(sent,message){
					if(sent){
						$(".messages").append(
							jQuery("<li>").html(
								"<b>Me</b>: " + message
							)
						);
						$(".compose-message-form").find("textarea").val("");

						var block = $("#block")[0];
						block.scrollTop = block.scrollHeight;
					}
				});
			}
		});

		chatAPI.onMessage = function(message){
			$(".messages").append(
				jQuery("<li>").html(
					"<b>" + message.sender + "</b>: " + message.content 
				)
			);
		};

	};

	var connectRoom = function(){
		bindUI();
		console.log("Welcome to Chat");
		chatAPI.connect(function(){});
		connectUser();
	};

	$(function(){ connectRoom(); });

}($,jQuery,window));