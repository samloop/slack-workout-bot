/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */
module.exports = function(controller) {

    // use a function to match a condition in the message
    controller.hears(async(message) => message.text && message.text.toLowerCase() === 'foo', ['message'], async (bot, message) => {
        await bot.reply(message, 'I heard "foo" via a function test');
    });

    // use a regular expression to match the text of the message
    controller.hears(new RegExp(/^\d+$/), ['message','direct_message'], async function(bot, message) {
        await bot.reply(message,{ text: 'I heard a number using a regular expression.' });
    });

    // match any one of set of mixed patterns like a string, a regular expression
    controller.hears(['allcaps', new RegExp(/^[A-Z\s]+$/)], ['message','direct_message'], async function(bot, message) {
        await bot.reply(message,{ text: 'I HEARD ALL CAPS!' });
    });


/*    if '!gym' in self._lower_text:
    self._points_to_add += self.GYM_POINTS
    self._additions.append('!gym')
    if '!track' in self._lower_text:
    self._points_to_add += self.TRACK_POINTS
    self._additions.append('!track')
    if '!throw' in self._lower_text:
    self._points_to_add += self.THROW_POINTS
    self._additions.append('!throw')
    if '!swim' in self._lower_text:
    self._points_to_add += self.SWIM_POINTS
    self._additions.append('!swim')
    if '!pickup' in self._lower_text:
    self._points_to_add += self.PICKUP_POINTS
    self._additions.append('!pickup')
    if '!bike' in self._lower_text:
    self._points_to_add += self.BIKING_POINTS
    self._additions.append('!bike')
    if '!run' in self._lower_text:
    self._points_to_add += self.BIKING_POINTS
    self._additions.append('!run')*/

}