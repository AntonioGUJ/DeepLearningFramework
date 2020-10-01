
from typing import Tuple, List, Dict, Union, Any

from tensorflow.keras.layers import Input, concatenate, Dropout, BatchNormalization
from tensorflow.keras.layers import Convolution3D, MaxPooling3D, UpSampling3D, Cropping3D, Conv3DTranspose
from tensorflow.keras.models import Model, load_model

from common.exceptionmanager import catch_error_exception
from models.networks import UNetBase

LIST_AVAIL_NETWORKS = ['UNet3D_Original',
                       'UNet3D_General',
                       'UNet3D_Plugin',
                       ]


class UNet(UNetBase):

    def __init__(self,
                 size_image_in: Tuple[int, ...],
                 num_levels: int,
                 num_featmaps_in: int,
                 num_channels_in: int,
                 num_classes_out: int,
                 is_use_valid_convols: bool = False
                 ) -> None:
        super(UNet, self).__init__(size_image_in, num_levels, num_featmaps_in, num_channels_in, num_classes_out,
                                   is_use_valid_convols=is_use_valid_convols)
        self._compiled_model = 0

    def get_compiled_model(self):
        return self._compiled_model

    def _build_list_info_crop_where_merge(self) -> None:
        indexes_output_where_pooling = [(i-1) for i, el in enumerate(self._list_opers_names_layers_all) if el == 'pooling']
        indexes_output_where_merge = [i for i, el in enumerate(self._list_opers_names_layers_all) if el == 'upsample']
        self._list_sizes_borders_crop_where_merge = []
        for i_pool, i_merge in zip(indexes_output_where_pooling, indexes_output_where_merge[::-1]):
            size_borders_crop_where_merge = self._get_size_borders_output_crop(self._list_sizes_output_all_layers[i_pool],
                                                                               self._list_sizes_output_all_layers[i_merge])
            self._list_sizes_borders_crop_where_merge.append(size_borders_crop_where_merge)


class UNet3D_Original(UNet):

    def __init__(self,
                 size_image_in: Tuple[int, int, int],
                 num_featmaps_in: int = 16,
                 num_channels_in: int = 1,
                 num_classes_out: int = 1
                 ) -> None:
        num_levels = 5
        super(UNet3D_Original, self).__init__(size_image_in, num_levels, num_featmaps_in, num_channels_in, num_classes_out,
                                              is_use_valid_convols=False)

        self._compiled_model = self._build_model()

    def _build_model(self) -> None:
        input_layer = Input((self._size_image_in) + (self._num_channels_in,))

        num_featmaps_lev1 = self._num_featmaps_in
        convolution_down_lev1_1 = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation='relu', padding='same')(input_layer)
        convolution_down_lev1_2 = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_down_lev1_1)
        pooling_down_lev1 = MaxPooling3D(pool_size=(2,2,2))(convolution_down_lev1_2)

        num_featmaps_lev2 = 2 * num_featmaps_lev1
        convolution_down_lev2_1 = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation='relu', padding='same')(pooling_down_lev1)
        convolution_down_lev2_2 = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_down_lev2_1)
        pooling_down_lev2 = MaxPooling3D(pool_size=(2,2,2))(convolution_down_lev2_2)

        num_featmaps_lev3 = 2 * num_featmaps_lev2
        convolution_down_lev3_1 = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation='relu', padding='same')(pooling_down_lev2)
        convolution_down_lev3_2 = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_down_lev3_1)
        pooling_down_lev3 = MaxPooling3D(pool_size=(2,2,2))(convolution_down_lev3_2)

        num_featmaps_lev4 = 2 * num_featmaps_lev3
        convolution_down_lev4_1 = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation='relu', padding='same')(pooling_down_lev3)
        convolution_down_lev4_2 = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_down_lev4_1)
        pooling_down_lev4 = MaxPooling3D(pool_size=(2,2,2))(convolution_down_lev4_2)

        num_featmaps_lev5 = 2 * num_featmaps_lev4
        convolution_down_lev5_1 = Convolution3D(num_featmaps_lev5, kernel_size=(3,3,3), activation='relu', padding='same')(pooling_down_lev4)
        convolution_down_lev5_2 = Convolution3D(num_featmaps_lev5, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_down_lev5_1)
        upsample_up_lev5 = UpSampling3D(size=(2,2,2))(convolution_down_lev5_2)

        upsample_up_lev5 = concatenate([upsample_up_lev5, convolution_down_lev4_2], axis=-1)
        convolution_up_lev4_1 = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation='relu', padding='same')(upsample_up_lev5)
        convolution_up_lev4_2 = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_up_lev4_1)
        upsample_up_lev4 = UpSampling3D(size=(2,2,2))(convolution_up_lev4_2)

        upsample_up_lev4 = concatenate([upsample_up_lev4, convolution_down_lev3_2], axis=-1)
        convolution_up_lev3_1 = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation='relu', padding='same')(upsample_up_lev4)
        convolution_up_lev3_2 = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_up_lev3_1)
        upsample_up_lev3 = UpSampling3D(size=(2,2,2))(convolution_up_lev3_2)

        upsample_up_lev3 = concatenate([upsample_up_lev3, convolution_down_lev2_2], axis=-1)
        convolution_up_lev2_1 = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation='relu', padding='same')(upsample_up_lev3)
        convolution_up_lev2_2 = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_up_lev2_1)
        upsample_up_lev2 = UpSampling3D(size=(2,2,2))(convolution_up_lev2_2)

        upsample_up_lev2 = concatenate([upsample_up_lev2, convolution_down_lev1_2], axis=-1)
        convolution_up_lev1_1 = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation='relu', padding='same')(upsample_up_lev2)
        convolution_up_lev1_2 = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation='relu', padding='same')(convolution_up_lev1_1)

        output_layer = Convolution3D(self._num_classes_out, kernel_size=(1,1,1), activation='sigmoid')(convolution_up_lev1_2)

        output_model = Model(inputs=input_layer, outputs=output_layer)
        return output_model


class UNet3D_General(UNet):
    _num_levels_default = 5
    _num_levels_non_padded = 3
    _num_featmaps_in_default = 16
    _num_channels_in_default = 1
    _num_classes_out_default = 1
    _dropout_rate_default = 0.2
    _type_activate_hidden_default = 'relu'
    _type_activate_output_default = 'sigmoid'
    _num_convols_levels_down_default = 2
    _num_convols_levels_up_default = 2
    _sizes_kernel_convol_levels_down_default = (3, 3, 3)
    _sizes_kernel_convol_levels_up_default = (3, 3, 3)
    _sizes_pooling_levels_default = (2, 2, 2)

    def __init__(self,
                 size_image_in: Tuple[int, int, int],
                 num_levels: int = _num_levels_default,
                 num_featmaps_in: int = _num_featmaps_in_default,
                 num_channels_in: int = _num_channels_in_default,
                 num_classes_out: int = _num_classes_out_default,
                 is_use_valid_convols: bool = False,
                 type_activate_hidden: str = _type_activate_hidden_default,
                 type_activate_output: str = _type_activate_output_default,
                 num_featmaps_levels: List[int] = None,
                 num_convols_levels_down: Union[int, Tuple[int, ...]] = _num_convols_levels_down_default,
                 num_convols_levels_up: Union[int, Tuple[int, ...]] = _num_convols_levels_up_default,
                 sizes_kernel_convol_levels_down: Union[Tuple[int, int, int], List[Tuple[int, int, int]]] = _sizes_kernel_convol_levels_down_default,
                 sizes_kernel_convol_levels_up: Union[Tuple[int, int, int], List[Tuple[int, int, int]]] = _sizes_kernel_convol_levels_up_default,
                 sizes_pooling_levels: Union[Tuple[int, int, int], List[Tuple[int, int, int]]] = _sizes_pooling_levels_default,
                 is_disable_convol_pooling_axialdim_lastlevel: bool = False,
                 is_use_dropout: bool = False,
                 dropout_rate: float = _dropout_rate_default,
                 is_use_dropout_levels_down: Union[bool, List[bool]] = True,
                 is_use_dropout_levels_up: Union[bool, List[bool]] = True,
                 is_use_batchnormalize=False,
                 is_use_batchnormalize_levels_down: Union[bool, List[bool]] = True,
                 is_use_batchnormalize_levels_up: Union[bool, List[bool]] = True
                 ) -> None:
        super(UNet, self).__init__(size_image_in, num_levels, num_featmaps_in, num_channels_in, num_classes_out,
                                   is_use_valid_convols=is_use_valid_convols)

        self._type_activate_hidden = type_activate_hidden
        self._type_activate_output = type_activate_output

        if num_featmaps_levels:
            self._num_featmaps_levels = num_featmaps_levels
        else:
            # default: double featmaps after every pooling
            self._num_featmaps_levels = [self._num_featmaps_in]
            for i in range(1, self._num_levels):
                self._num_featmaps_levels[i] = 2 * self._num_featmaps_levels[i-1]

        if type(num_convols_levels_down) == int:
            self._num_convols_levels_down = [num_convols_levels_down] * self._num_levels
        else:
            self._num_convols_levels_down = num_convols_levels_down
        if type(num_convols_levels_up) == int:
            self._num_convols_levels_up = [num_convols_levels_up] * (self._num_levels-1)
        else:
            self._num_convols_levels_up = num_convols_levels_up

        if type(sizes_kernel_convol_levels_down) == tuple:
            self._sizes_kernel_convol_levels_down = [sizes_kernel_convol_levels_down] * self._num_levels
        else:
            self._sizes_kernel_convol_levels_down = sizes_kernel_convol_levels_down
        if type(sizes_kernel_convol_levels_up) == tuple:
            self._sizes_kernel_convol_levels_up = [sizes_kernel_convol_levels_up] * (self._num_levels-1)
        else:
            self._sizes_kernel_convol_levels_up = sizes_kernel_convol_levels_up

        if type(sizes_pooling_levels) == tuple:
            self._sizes_pooling_levels = [sizes_pooling_levels] * self._num_levels
        else:
            self._sizes_pooling_levels = sizes_pooling_levels
        self._sizes_upsample_levels = self._sizes_pooling_levels[:-1]

        if is_disable_convol_pooling_axialdim_lastlevel:
            size_kernel_convol_lastlevel = self._sizes_kernel_convol_levels_down[-1]
            self._sizes_kernel_convol_levels_down[-1] = (1, size_kernel_convol_lastlevel[1], size_kernel_convol_lastlevel[2])
            size_pooling_lastlevel = self._sizes_pooling_levels[-1]
            self._sizes_pooling_levels[-1] = (1, size_pooling_lastlevel[1], size_pooling_lastlevel[2])

        self._is_use_dropout = is_use_dropout
        if is_use_dropout:
            self._dropout_rate = dropout_rate

            if type(is_use_dropout_levels_down) == bool:
                self._is_use_dropout_levels_down = [is_use_dropout_levels_down] * self._num_levels
            else:
                self._is_use_dropout_levels_down = is_use_dropout_levels_down
            if type(is_use_dropout_levels_up) == bool:
                self._is_use_dropout_levels_up = [is_use_dropout_levels_up] * (self._num_levels-1)
            else:
                self._is_use_dropout_levels_up = is_use_dropout_levels_up

        self._is_use_batchnormalize = is_use_batchnormalize
        if is_use_batchnormalize:
            if type(is_use_batchnormalize_levels_down) == bool:
                self._is_use_batchnormalize_levels_down = [is_use_batchnormalize_levels_down] * self._num_levels
            else:
                self._is_use_batchnormalize_levels_down = is_use_batchnormalize_levels_down
            if type(is_use_batchnormalize_levels_up) == bool:
                self._is_use_batchnormalize_levels_up = [is_use_batchnormalize_levels_up] * (self._num_levels-1)
            else:
                self._is_use_batchnormalize_levels_up = is_use_batchnormalize_levels_up

        self._compiled_model = self._build_model()

    def _build_model(self) -> None:
        type_padding_convols = 'valid' if self._is_use_valid_convols else 'same'

        input_layer = Input((self._size_image_in) + (self._num_channels_in,))
        hidden_next = input_layer
        list_skipconn_levels = []

        # ENCODING LAYERS
        for i_lev in range(self._num_levels):
            for i_con in range(self._num_convols_levels_down[i_lev]):
                hidden_next = Convolution3D(self._num_featmaps_levels[i_lev],
                                            kernel_size=self._sizes_kernel_convol_levels_down[i_lev],
                                            activation=self._type_activate_hidden,
                                            padding=type_padding_convols)(hidden_next)

                if self._is_use_batchnormalize and self._is_use_batchnormalize_levels_down[i_lev]:
                    hidden_next = BatchNormalization()(hidden_next)

            if self._is_use_dropout and self._is_use_dropout_levels_down[i_lev]:
                hidden_next = Dropout(self._dropout_rate)(hidden_next)

            if (i_lev != self._num_levels-1):
                list_skipconn_levels.append(hidden_next)
                hidden_next = MaxPooling3D(pool_size=self._sizes_pooling_levels[i_lev])(hidden_next)

        # DECODING LAYERS
        for i_lev in range(self._num_levels-2, -1, -1):
            hidden_next = UpSampling3D(size=self._sizes_upsample_levels[i_lev])(hidden_next)

            skipconn_thislev = list_skipconn_levels[i_lev]
            if self._is_use_valid_convols:
                skipconn_thislev = Cropping3D(cropping=self._list_sizes_borders_crop_where_merge[i_lev])(skipconn_thislev)
            hidden_next = concatenate([hidden_next, skipconn_thislev], axis=-1)

            for i_con in range(self._num_convols_levels_up[i_lev]):
                hidden_next = Convolution3D(self._num_featmaps_levels[i_lev],
                                            kernel_size=self._sizes_kernel_convol_levels_up[i_lev],
                                            activation=self._type_activate_hidden,
                                            padding=type_padding_convols)(hidden_next)

                if self._is_use_batchnormalize and self._is_use_batchnormalize_levels_up[i_lev]:
                    hidden_next = BatchNormalization()(hidden_next)

            if self._is_use_dropout and self._is_use_dropout_levels_up[i_lev]:
                hidden_next = Dropout(self._dropout_rate)(hidden_next)

        output_layer = Convolution3D(self._num_classes_out, kernel_size=(1,1,1), activation=self._type_activate_output)(hidden_next)

        output_model = Model(inputs=input_layer, outputs=output_layer)
        return output_model


class UNet3D_Plugin(UNet):
    _num_levels_default = 5
    _num_levels_non_padded = 3
    _num_featmaps_in_default = 16
    _num_channels_in_default = 1
    _num_classes_out_default = 1
    _dropout_rate_default = 0.2
    _type_activate_hidden_default = 'relu'
    _type_activate_output_default = 'sigmoid'

    def __init__(self,
                 size_image_in: Tuple[int, int, int],
                 num_levels: int = _num_levels_default,
                 num_featmaps_in: int = _num_featmaps_in_default,
                 num_channels_in: int = _num_channels_in_default,
                 num_classes_out: int = _num_classes_out_default,
                 is_use_valid_convols: bool = False
                 ) -> None:
        super(UNet3D_Plugin, self).__init__(size_image_in, num_levels, num_featmaps_in, num_channels_in, num_classes_out,
                                            is_use_valid_convols=is_use_valid_convols)

        self._type_activate_hidden = self._type_activate_hidden_default
        self._type_activate_output = self._type_activate_output_default

        self._compiled_model = self._build_model()

    def _build_model(self) -> None:
        type_padding = 'valid' if self._is_use_valid_convols else 'same'

        input_layer = Input((self._size_image_in) + (self._num_channels_in,))

        num_featmaps_lev1 = self._num_featmaps_in
        hidden_next = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(input_layer)
        hidden_next = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        skipconn_lev1 = hidden_next
        hidden_next = MaxPooling3D(pool_size=(2,2,2))(hidden_next)

        num_featmaps_lev2 = 2 * num_featmaps_lev1
        hidden_next = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        skipconn_lev2 = hidden_next
        hidden_next = MaxPooling3D(pool_size=(2,2,2))(hidden_next)

        num_featmaps_lev3 = 2 * num_featmaps_lev2
        hidden_next = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        skipconn_lev3 = hidden_next
        hidden_next = MaxPooling3D(pool_size=(2,2,2))(hidden_next)

        num_featmaps_lev4 = 2 * num_featmaps_lev3
        hidden_next = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        skipconn_lev4 = hidden_next
        hidden_next = MaxPooling3D(pool_size=(2,2,2))(hidden_next)

        num_featmaps_lev5 = 2 * num_featmaps_lev4
        hidden_next = Convolution3D(num_featmaps_lev5, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev5, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        hidden_next = UpSampling3D(size=(2,2,2))(hidden_next)

        if self._is_use_valid_convols:
            skipconn_lev4 = Cropping3D(cropping= self._list_sizes_borders_crop_where_merge[3])(skipconn_lev4)
        hidden_next = concatenate([hidden_next, skipconn_lev4], axis=-1)
        hidden_next = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev4, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding='same')(hidden_next)
        hidden_next = UpSampling3D(size=(2,2,2))(hidden_next)

        if self._is_use_valid_convols:
            skipconn_lev3 = Cropping3D(cropping= self._list_sizes_borders_crop_where_merge[2])(skipconn_lev3)
        hidden_next = concatenate([hidden_next, skipconn_lev3], axis=-1)
        hidden_next = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev3, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = UpSampling3D(size=(2,2,2))(hidden_next)

        if self._is_use_valid_convols:
            skipconn_lev2 = Cropping3D(cropping= self._list_sizes_borders_crop_where_merge[1])(skipconn_lev2)
        hidden_next = concatenate([hidden_next, skipconn_lev2], axis=-1)
        hidden_next = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev2, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = UpSampling3D(size=(2,2,2))(hidden_next)

        if self._is_use_valid_convols:
            skipconn_lev1 = Cropping3D(cropping=self._list_sizes_borders_crop_where_merge[0])(skipconn_lev1)
        hidden_next = concatenate([hidden_next, skipconn_lev1], axis=-1)
        hidden_next = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)
        hidden_next = Convolution3D(num_featmaps_lev1, kernel_size=(3,3,3), activation=self._type_activate_hidden, padding=type_padding)(hidden_next)

        output_layer = Convolution3D(self._num_classes_out, kernel_size=(1,1,1), activation=self._type_activate_output)(hidden_next)

        output_model = Model(inputs=input_layer, outputs=output_layer)
        return output_model