# JetFormBuilder PHP Hooks — verified reference

Source: official plugin wiki
https://github.com/Crocoblock/jetformbuilder/wiki/PHP-Hooks

Only hooks confirmed in the primary source are listed here.

## Actions

### `jet-form-builder/custom-action/{$hook_name}`
Fires only when the form has a Post-Submit Action of type "Call Hook" with
the matching name. Runs in sequence with the form's other actions.

Params: `$request` (array, submitted data), `$handler`
(`\Jet_Form_Builder\Actions\Action_Handler`)

This is the only fully flexible mechanism for custom logic in JetFormBuilder.
It covers both "do something after submit" and "blocking validation": throwing
`\Jet_Form_Builder\Exceptions\Action_Exception` inside the callback stops all
remaining actions and returns an error to the user.

Built-in error statuses for `Action_Exception`: `success`, `failed`,
`validation_failed`, `captcha_failed`, `invalid_email`, `empty_field`,
`internal_error`, `upload_max_files`, `upload_max_size`, `upload_mime_types`.
An arbitrary string is also accepted and shown as the error text.

For validation to block submission, the Call Hook action must be placed
FIRST in the form's Post-Submit Actions list.

Example:
```php
add_action(
    'jet-form-builder/custom-action/test_action',
    function ( $request, $handler ) {
        if ( empty( $request['age'] ) ) {
            throw new \Jet_Form_Builder\Exceptions\Action_Exception( 'empty_field' );
        }
        if ( absint( $request['age'] ) < 18 ) {
            throw new \Jet_Form_Builder\Exceptions\Action_Exception( 'Your age is less than necessary' );
        }
    },
    10,
    2
);
```

### `jet-form-builder/action/after-post-insert`
Fires after a new post is created by the Insert/Update Post action.

Params: `$action` (`\Jet_Form_Builder\Actions\Types\Base`), `$handler`

The inserted post ID is retrieved with
`$handler->get_inserted_post_id( $action->_id )`.

### `jet-form-builder/action/webhook/response`
Fires after a successful `wp_remote_post` in the Call Webhook action.

Params: `$response` (array), `$settings` (array), `$action`

### `jet-form-builder/form-handler/before-send` and `after-send`
Fire before and after all actions during a normal submission.

Params (before-send): `$handler` (`\Jet_Form_Builder\Form_Handler`)
Params (after-send): `$handler`, `$is_success` (bool)

## Filters

### `jet-form-builder/fields/wysiwyg-field/config`
Alters settings passed to `wp_editor()` for the WYSIWYG field.
Params: `$config` (array). Must return `$config`.

### `jet-form-builder/editor/hidden-field/config`
Adds entries to the "Field Value" source list of the Hidden Field in the
form editor. Params: `$config` (array). Must return `$config`.

### `jet-form-builder/fields/hidden-field/value-cb`
Returns a callable that produces the value for a hidden field with a given
`field_value`. Params: `$callback` (false|callable), `$field_value` (string).

### `jet-form-builder/send-email/template-repeater`
Alters repeater output in the Send Email action.
Params: `$content` (string), `$items` (array).

## Unverified

`jet-form-builder/option-query/set-in-block` appears in changelogs but is NOT
confirmed in the official wiki. Its signature and firing point are unknown.
Never present code using this hook as guaranteed to work.