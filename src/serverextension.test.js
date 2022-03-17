const serverextension = require('./serverextension');

describe('serverextension', () => {
    test('can import successfully', () => {
        expect(serverextension).toBeDefined();
    });
});
