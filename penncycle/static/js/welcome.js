$(function() {
	$(".renew").click(function() {
		var id = $(this).closest('[id]').attr('id');
		$.post(
			"/modify_payment/",
			{"id": id, "action": "renew"},
			function(result) {
				$("#payment_message").html("Successfully enabled renewal.").delay(1000);
				location.reload();
			}
			);
	});
	$(".disable").click(function() {
		var id = $(this).closest('[id]').attr('id');
		$.post(
			"/modify_payment/",
			{"id": id, "action": "disable"},
			function(result) {
				$("#payment_message").html("Successfully disabled renewal.").delay(1000);
				location.reload();
			});
	});
	$(".delete").click(function() {
		if(confirm("Are you sure you want to delete this payment?")) {
			var id = $(this).closest('[id]').attr('id');
			$.post(
				"/modify_payment/",
				{"id": id, "action": "delete"},
				function(result) {
					$("#payment_message").html("Successfully deleted payment.").delay(1000);
					location.reload();
				});
		}
	});
	$(".pay_by_credit").click(function() {
		var id = $(this).closest('[id]').attr('id');
		var base = $(this).attr("amount");
		var amount = 1.08 * base;
		$("#payment_id").val(id);
		$("#amount_id").val(amount);
		$("#vpul_form").submit();
		$("#vpul_iframe").height(800);
		$("#payment_info").hide();
	});
});
$("#accept").click(function() {
	$.post(
		"/verify_waiver/",
		{}, // The penncard is in the session... sketchy though
		function(data) {
		if (data.success) {
			$("#waiver-result").html("Successfully submitted waiver.");
		} else {
			$("#waiver-result").html("There was a problem with our server. Reloading data...");
		}
		location.reload();
	}
	);
});
function toggle_renew() {
	if ($("input[name=payment]:checked").val() == "bursar") {
		if ($("#plan_name").html() != "Day") {
			$("#renew-select").show();
		} else {
			$("#renew-select").hide();
		}
	} else {
		$("#renew-select").hide();
	}
}
$(".circle").click(function() {
	$(this).addClass("selected");
	$(".circle").not(this).removeClass("selected");
	$("#purchase_button").removeClass("disabled");
	switch (this.id) {
		case "day_plan":
		$("#subtotal").html("3");
		$("#tax").html("0.24");
		$("#total").html("3.24");
		$("#purchase_button").html("Purchase Day Plan");
		$("#plan_name").html("Day");
		break;
		case "basic_plan":
		$("#subtotal").html("9");
		$("#tax").html("0.72");
		$("#total").html("9.72");
		$("#purchase_button").html("Purchase Basic Plan");
		$("#plan_name").html("Basic");
		break;
		case "unlimited_plan":
		$("#subtotal").html("29");
		$("#tax").html("2.32");
		$("#total").html("31.32");
		$("#purchase_button").html("Purchase Unlimited Plan");
		$("#plan_name").html("Unlimited");
		break;
	}
	toggle_renew();
});
$("input[type='radio']").click(function() {
	var desc = $(this).val();
	var target = $("#" + desc + "_description");
	$(".descriptions p").not(target).addClass("hidden");
	target.removeClass("hidden");
	toggle_renew();
});

$("#purchase_button").click(function() {
	if ($(this).hasClass("disabled")) {
		return;
	}
	method = $("input[name=payment]:checked").val();
	var data = {
		"penncard": "{{ student.penncard }}",
		"renew": $("#renew").is(':checked'),
		"plan": $(".selected")[0].id
	};
	if (method == "credit") {
		var total = $("#total").html();
		$("#amount_id").val(total);
		$.ajax({
			type: "POST",
			url: "/credit/",
			data: data,
			success: function(payment_id) {
				$("#payment_id").val(payment_id);
				$("#vpul_form").submit();
				$("#vpul_iframe").height(800);
				$("#payment_info").hide();
			},
			error: function (error) {
				alert(error);
			}
		});
	} else {
		$.ajax({
			type: "POST",
			url: "/" + method + "/",
			data: data,
			success: function() {
				location.reload();
			},
			error: function (error) {
				alert("Unable to connect. Check your internet connection.");
			},
			async: false
		});
	}
});