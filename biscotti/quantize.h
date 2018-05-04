/*
 * Copyright 2018 Taichi Nishimura
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef GUETZLI_QUANTIZE_H_
#define GUETZLI_QUANTIZE_H_

#include "biscotti/jpeg_data.h"

namespace biscotti {

inline coeff_t Quantize(coeff_t raw_coeff, int quant) {
  const int r = raw_coeff % quant;
  const coeff_t delta =
      2 * r > quant ? quant - r : (-2) * r > quant ? -quant - r : -r;
  return raw_coeff + delta;
}

bool QuantizeBlock(coeff_t block[kDCTBlockSize], const int q[kDCTBlockSize]);

}  // namespace biscotti

#endif  // GUETZLI_QUANTIZE_H_
