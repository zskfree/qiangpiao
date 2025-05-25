// 通用工具函数
function showAlert(type, message) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertContainer, container.firstChild);

    // 自动消失
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.remove();
        }
    }, 5000);
}

// 格式化时间
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 验证时间格式
function validateTimeSlot(timeSlot) {
    const timePattern = /^([01]?[0-9]|2[0-3]):[0-5][0-9]-([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    return timePattern.test(timeSlot);
}

// 日期格式化
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// 获取明天的日期
function getTomorrowDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return formatDate(tomorrow);
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 自动设置明天的日期（如果日期输入框为空）
    const dateInput = document.querySelector('input[name="TARGET_DATE"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = getTomorrowDate();
    }

    // 为所有表单添加提交确认
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (this.id === 'configForm') {
                // 验证配置表单
                const timeSlots = document.querySelector('textarea[name="PREFERRED_TIMES"]').value.split('\n');
                const invalidSlots = timeSlots.filter(slot => slot.trim() && !validateTimeSlot(slot.trim()));

                if (invalidSlots.length > 0) {
                    e.preventDefault();
                    showAlert('danger', '时间格式错误: ' + invalidSlots.join(', '));
                    return;
                }
            }
        });
    });
});

// 复制到剪贴板功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function () {
        showAlert('success', '已复制到剪贴板');
    }, function (err) {
        showAlert('danger', '复制失败');
    });
}
