console.log('TEST: Basic JavaScript is working');

// Test if ContactDetailJS exists
if (typeof ContactDetailJS !== 'undefined') {
    console.log('TEST: ContactDetailJS object exists');
} else {
    console.log('TEST: ContactDetailJS object does NOT exist');
}

// Test basic initialization
try {
    console.log('TEST: About to call ContactDetailJS.init(4)');
    if (typeof ContactDetailJS !== 'undefined' && ContactDetailJS.init) {
        ContactDetailJS.init(4);
        console.log('TEST: ContactDetailJS.init() completed');
    } else {
        console.log('TEST: ContactDetailJS.init is not available');
    }
} catch (error) {
    console.error('TEST: Error calling ContactDetailJS.init:', error);
}